"""Time-split offline evaluation for InstaKill feed strategies."""

import argparse
import base64
import csv
import hashlib
import html
import io
import math
import sqlite3
import subprocess
import tempfile
from collections import defaultdict
from contextlib import closing
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

from app.db.database import DB_PATH, get_connection
from app.services import feed as feed_service

ROOT = Path(__file__).resolve().parents[1]
STRATEGIES = ("chronological", "popularity", "for_you", "learned")
DISCOUNT = np.asarray(
    [1.0 / math.log2(rank + 2) for rank in range(10)]
)
STRATEGY_COLORS = {
    "chronological": "#4477AA",
    "popularity": "#EE6677",
    "for_you": "#228833",
    "learned": "#AA3377",
}
GROUPS = ("new", "casual", "regular", "power")


def _popularity_scorer(features: np.ndarray) -> np.ndarray:
    return features[:, 1]


def parse_cutoff(value: str) -> datetime:
    try:
        if "T" not in value and " " not in value:
            parsed = datetime.combine(date.fromisoformat(value), time.min)
        else:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "cutoff must be an ISO date or datetime"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def default_cutoff(connection: sqlite3.Connection) -> datetime:
    timestamps = [
        row[0]
        for row in connection.execute(
            "SELECT created_at FROM post_like ORDER BY created_at, user_id, post_id"
        )
    ]
    if not timestamps:
        raise ValueError("cannot determine a default cutoff: database has no likes")
    index = max(0, math.ceil(0.8 * len(timestamps)) - 1)
    return parse_cutoff(str(timestamps[index]))


def build_snapshot(source_path: Path, snapshot_path: Path, cutoff: datetime) -> None:
    """Copy the database and retain only state available strictly before cutoff."""
    source = get_connection(source_path)
    snapshot = sqlite3.connect(snapshot_path)
    snapshot.row_factory = sqlite3.Row
    snapshot.execute("PRAGMA foreign_keys = ON")
    try:
        source.backup(snapshot)
        cutoff_text = _iso(cutoff)
        with snapshot:
            snapshot.execute("DELETE FROM follow")
            future_posts = "(SELECT id FROM post WHERE created_at >= ?)"
            snapshot.execute(
                f"DELETE FROM post_like WHERE created_at >= ? OR post_id IN {future_posts}",
                (cutoff_text, cutoff_text),
            )
            snapshot.execute(
                f"DELETE FROM rating WHERE created_at >= ? OR post_id IN {future_posts}",
                (cutoff_text, cutoff_text),
            )
            snapshot.execute("DELETE FROM post WHERE created_at >= ?", (cutoff_text,))
            snapshot.execute(
                """
                INSERT INTO follow (follower_id, followee_id, created_at)
                SELECT l.user_id, p.user_id, MIN(l.created_at)
                FROM post_like AS l JOIN post AS p ON p.id = l.post_id
                WHERE l.user_id != p.user_id
                GROUP BY l.user_id, p.user_id
                """
            )
    finally:
        source.close()
        snapshot.close()


def ndcg_at_10(ranked_post_ids: Iterable[int], relevant_post_ids: set[int]) -> float:
    if not relevant_post_ids:
        return 0.0
    dcg = sum(
        DISCOUNT[index]
        for index, post_id in enumerate(list(ranked_post_ids)[:10])
        if post_id in relevant_post_ids
    )
    ideal_dcg = float(DISCOUNT[: min(10, len(relevant_post_ids))].sum())
    return float(dcg / ideal_dcg)


def _user_group(like_count: int) -> str:
    if like_count < 10:
        return "new"
    if like_count < 50:
        return "casual"
    if like_count < 200:
        return "regular"
    return "power"


def _paired_interval(
    values: np.ndarray, rng: np.random.Generator
) -> tuple[float, float]:
    if not len(values):
        return float("nan"), float("nan")
    if len(values) == 1:
        value = float(values[0])
        return value, value
    indices = rng.integers(0, len(values), size=(5000, len(values)))
    means = values[indices].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "scripts/evaluate.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        return result.stdout.strip()
    fallback = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return fallback.stdout.strip()


def _fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(
    db_path: Path,
    cutoff: datetime,
    seed: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    with closing(get_connection(db_path)) as source:
        cutoff_text = _iso(cutoff)
        with tempfile.TemporaryDirectory(prefix="instakill-eval-") as directory:
            snapshot_path = Path(directory) / "snapshot.sqlite"
            build_snapshot(db_path, snapshot_path, cutoff)
            snapshot = get_connection(snapshot_path)
            try:
                before_counts = {
                    int(row["user_id"]): int(row["n"])
                    for row in snapshot.execute(
                        """
                        SELECT user_id, COUNT(*) AS n FROM post_like
                        WHERE created_at < ? GROUP BY user_id
                        """,
                        (cutoff_text,),
                    )
                }
                available_posts = {
                    int(row["id"])
                    for row in snapshot.execute("SELECT id FROM post")
                }
                after_by_user: dict[int, set[int]] = defaultdict(set)
                for row in source.execute(
                    """
                    SELECT l.user_id, l.post_id
                    FROM post_like AS l JOIN post AS p ON p.id = l.post_id
                    WHERE l.created_at >= ? AND p.created_at < ?
                    """,
                    (cutoff_text, cutoff_text),
                ):
                    user_id, post_id = int(row["user_id"]), int(row["post_id"])
                    if post_id in available_posts:
                        after_by_user[user_id].add(post_id)

                users = sorted(
                    user_id
                    for user_id, count in before_counts.items()
                    if count >= 3 and after_by_user.get(user_id)
                )
                groups = {
                    user_id: _user_group(before_counts[user_id]) for user_id in users
                }
                rows: list[dict[str, object]] = []
                for user_id in users:
                    relevant = after_by_user[user_id]
                    for strategy in STRATEGIES:
                        ranked = feed_service.rank_feed(
                            user_id=user_id,
                            strategy=strategy,
                            limit=10,
                            now=cutoff,
                            connection=snapshot,
                            scorer=(
                                _popularity_scorer
                                if strategy == "popularity"
                                else None
                            ),
                        )
                        rows.append(
                            {
                                "user_id": user_id,
                                "strategy": strategy,
                                "ndcg_at_10": ndcg_at_10(
                                    (item.post_id for item in ranked), relevant
                                ),
                                "n_relevant": len(relevant),
                                "user_group": groups[user_id],
                            }
                        )
            finally:
                snapshot.close()

    metadata = {
        "cutoff": cutoff_text,
        "seed": seed,
        "n_users": len(users),
        "database_fingerprint": _fingerprint(db_path),
        "git_commit": _git_commit(),
        "before_counts": before_counts,
    }
    return rows, metadata


def _summary(
    rows: list[dict[str, object]], seed: int
) -> tuple[
    dict[str, tuple[float, float, float, int]],
    dict[str, tuple[float, float, float, int, str]],
]:
    rng = np.random.default_rng(seed)
    overall: dict[str, tuple[float, float, float, int]] = {}
    deltas: dict[str, tuple[float, float, float, int, str]] = {}
    values_by_user_strategy = {
        (int(row["user_id"]), str(row["strategy"])): float(row["ndcg_at_10"])
        for row in rows
    }
    users = sorted({int(row["user_id"]) for row in rows})
    for strategy in STRATEGIES:
        values = np.asarray(
            [values_by_user_strategy[(user_id, strategy)] for user_id in users]
        )
        low, high = _paired_interval(values, rng)
        overall[strategy] = (
            float(values.mean()) if len(values) else float("nan"),
            low,
            high,
            len(values),
        )
    baselines = STRATEGIES[:-1]
    best_baseline = max(baselines, key=lambda key: overall[key][0]) if users else None
    if best_baseline is not None:
        difference = np.asarray(
            [
                values_by_user_strategy[(user_id, "learned")]
                - values_by_user_strategy[(user_id, best_baseline)]
                for user_id in users
            ]
        )
        low, high = _paired_interval(difference, rng)
        deltas["overall"] = (
            float(difference.mean()),
            low,
            high,
            len(difference),
            best_baseline,
        )
    else:
        deltas["overall"] = (
            float("nan"),
            float("nan"),
            float("nan"),
            0,
            "n/a",
        )

    group_for_user = {
        int(row["user_id"]): str(row["user_group"]) for row in rows
    }
    for group in GROUPS:
        group_users = [
            user_id for user_id in users if group_for_user[user_id] == group
        ]
        if not group_users:
            deltas[group] = (
                float("nan"),
                float("nan"),
                float("nan"),
                0,
                "n/a",
            )
            continue
        best = max(
            baselines,
            key=lambda strategy: np.mean(
                [values_by_user_strategy[(user_id, strategy)] for user_id in group_users]
            ),
        )
        difference = np.asarray(
            [
                values_by_user_strategy[(user_id, "learned")]
                - values_by_user_strategy[(user_id, best)]
                for user_id in group_users
            ]
        )
        low, high = _paired_interval(difference, rng)
        deltas[group] = (float(difference.mean()), low, high, len(difference), best)
    return overall, deltas


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(
            ["user_id", "strategy", "ndcg_at_10", "n_relevant", "user_group"]
        )
        for row in rows:
            writer.writerow(
                [
                    row["user_id"],
                    row["strategy"],
                    format(float(row["ndcg_at_10"]), ".12g"),
                    row["n_relevant"],
                    row["user_group"],
                ]
            )


def _number(value: float) -> str:
    return "n/a" if math.isnan(value) else f"{value:.4f}"


def _interval(low: float, high: float) -> str:
    if math.isnan(low) or math.isnan(high):
        return "n/a"
    return f"[{low:.4f}, {high:.4f}]"


def _verdict(low: float, high: float) -> str:
    if math.isnan(low) or math.isnan(high):
        return "n/a"
    if low > 0:
        return "wins"
    if high < 0:
        return "loses"
    return "unclear"


def _write_markdown(
    path: Path,
    metadata: dict[str, object],
    overall: dict[str, tuple[float, float, float, int]],
    deltas: dict[str, tuple[float, float, float, int, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Offline feed evaluation",
        "",
        "## Baselines",
        "",
        "| Strategy | Mean NDCG@10 | 95% paired bootstrap interval | Users |",
        "|---|---:|:---:|---:|",
    ]
    for strategy in STRATEGIES:
        mean, low, high, count = overall[strategy]
        lines.append(
            f"| {strategy} | {_number(mean)} | {_interval(low, high)} | {count} |"
        )
    lines.extend(
        [
            "",
            "## Learned minus best baseline",
            "",
            "| Slice | Best baseline | Difference | 95% paired bootstrap interval | Verdict | Users |",
            "|---|---|---:|:---:|:---:|---:|",
        ]
    )
    for slice_name, (mean, low, high, count, baseline) in deltas.items():
        lines.append(
            f"| {slice_name} | {baseline} | {_number(mean)} | {_interval(low, high)} "
            f"| {_verdict(low, high)} | {count} |"
        )
    lines.extend(
        [
            "",
            "## Run metadata",
            "",
            f"- Cut-off (UTC): `{metadata['cutoff']}`",
            f"- Bootstrap seed: `{metadata['seed']}`",
            f"- Evaluated users: `{metadata['n_users']}`",
            f"- Database SHA-256: `{metadata['database_fingerprint']}`",
            f"- Git commit: `{metadata['git_commit']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _chart_png(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _dashboard(
    path: Path,
    metadata: dict[str, object],
    overall: dict[str, tuple[float, float, float, int]],
    deltas: dict[str, tuple[float, float, float, int, str]],
    rows: list[dict[str, object]],
) -> None:
    labels = list(STRATEGIES)
    means = [overall[name][0] for name in labels]
    lower = [means[i] - overall[name][1] for i, name in enumerate(labels)]
    upper = [overall[name][2] - means[i] for i, name in enumerate(labels)]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, means, color=[STRATEGY_COLORS[name] for name in labels])
    if means and not any(math.isnan(value) for value in means):
        ax.errorbar(
            labels,
            means,
            yerr=[lower, upper],
            fmt="none",
            ecolor="#222222",
            capsize=5,
        )
    ax.set_ylim(0, 1)
    ax.set_ylabel("Mean NDCG@10")
    ax.set_title("Which strategy ranks future likes highest overall?")
    ax.grid(axis="y", alpha=0.25)
    chart_one = _chart_png(fig)

    delta_labels = list(deltas)
    delta_means = [deltas[name][0] for name in delta_labels]
    delta_low = [deltas[name][1] for name in delta_labels]
    delta_high = [deltas[name][2] for name in delta_labels]
    span = max([abs(value) for value in delta_means + delta_low + delta_high] + [0.01])
    norm = TwoSlopeNorm(vmin=-span, vcenter=0, vmax=span)
    cmap = plt.get_cmap("coolwarm")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for index, (mean, low, high) in enumerate(zip(delta_means, delta_low, delta_high)):
        if math.isnan(mean):
            continue
        ax.errorbar(
            mean,
            index,
            xerr=[[mean - low], [high - mean]],
            fmt="o",
            color=cmap(norm(mean)),
            capsize=5,
        )
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_yticks(range(len(delta_labels)), delta_labels)
    ax.set_xlabel("Learned minus best baseline NDCG@10")
    ax.set_title("Where does learned beat the best baseline?")
    ax.grid(axis="x", alpha=0.25)
    chart_two = _chart_png(fig)

    group_means: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        group_means[(str(row["user_group"]), str(row["strategy"]))].append(
            float(row["ndcg_at_10"])
        )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    visible_groups = [
        group
        for group in GROUPS
        if any((group, strategy) in group_means for strategy in STRATEGIES)
    ]
    rng = np.random.default_rng(int(metadata["seed"]))
    for strategy in STRATEGIES:
        x_values, y_values, y_errors = [], [], []
        for position, group in enumerate(visible_groups):
            values = np.asarray(group_means.get((group, strategy), []), dtype=float)
            if not len(values):
                continue
            low, high = _paired_interval(values, rng)
            mean = float(values.mean())
            x_values.append(position)
            y_values.append(mean)
            y_errors.append([mean - low, high - mean])
        if x_values:
            yerr = np.asarray(y_errors).T
            ax.errorbar(
                x_values,
                y_values,
                yerr=yerr,
                marker="o",
                capsize=4,
                color=STRATEGY_COLORS[strategy],
                label=strategy,
            )
    ax.set_xticks(range(len(visible_groups)), visible_groups)
    ax.set_ylim(0, 1)
    ax.set_xlabel("User activity before cutoff")
    ax.set_ylabel("Mean NDCG@10")
    ax.set_title("How does ranking quality vary with user activity?")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    chart_three = _chart_png(fig)

    metadata_items = "".join(
        f"<li><strong>{html.escape(label)}:</strong> {html.escape(str(value))}</li>"
        for label, value in (
            ("Cut-off (UTC)", metadata["cutoff"]),
            ("Bootstrap seed", metadata["seed"]),
            ("Evaluated users", metadata["n_users"]),
            ("Database SHA-256", metadata["database_fingerprint"]),
            ("Git commit", metadata["git_commit"]),
        )
    )
    table_rows = "".join(
        "<tr>"
        f"<td>{html.escape(strategy)}</td>"
        f"<td>{_number(overall[strategy][0])}</td>"
        f"<td>{_interval(overall[strategy][1], overall[strategy][2])}</td>"
        f"<td>{overall[strategy][3]}</td>"
        "</tr>"
        for strategy in STRATEGIES
    )
    delta_rows = "".join(
        "<tr>"
        f"<td>{html.escape(slice_name)}</td>"
        f"<td>{html.escape(baseline)}</td>"
        f"<td>{_number(mean)}</td>"
        f"<td>{_interval(low, high)}</td>"
        f"<td>{_verdict(low, high)}</td>"
        f"<td>{count}</td>"
        "</tr>"
        for slice_name, (mean, low, high, count, baseline) in deltas.items()
    )
    sections = [
        ("Which strategy ranks future likes highest overall?", chart_one),
        ("Where does learned beat the best baseline?", chart_two),
        ("How does ranking quality vary with user activity?", chart_three),
    ]
    charts_html = "".join(
        f'<section><h2>{html.escape(title)}</h2><img alt="{html.escape(title)}" '
        f'src="data:image/png;base64,{image}"></section>'
        for title, image in sections
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>InstaKill offline feed evaluation</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#222}}
table{{border-collapse:collapse}}th,td{{padding:.5rem 1rem;border:1px solid #bbb;text-align:left}}
img{{display:block;width:100%;height:auto}}section{{margin:2rem 0}}code{{overflow-wrap:anywhere}}
</style></head><body>
<h1>InstaKill offline feed evaluation</h1>
<h2>Run metadata</h2><ul>{metadata_items}</ul>
<h2>Baseline table</h2><table><thead><tr><th>Strategy</th><th>Mean NDCG@10</th>
<th>95% paired bootstrap interval</th><th>Users</th></tr></thead><tbody>{table_rows}</tbody></table>
<h2>Learned minus best baseline</h2><table><thead><tr><th>Slice</th><th>Best baseline</th>
<th>Difference</th><th>95% paired bootstrap interval</th><th>Verdict</th><th>Users</th>
</tr></thead><tbody>{delta_rows}</tbody></table>
{charts_html}</body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8", newline="\n")


def run_evaluation(
    db_path: Path,
    out_dir: Path,
    cutoff: datetime | None = None,
    seed: int = 42,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    with closing(get_connection(db_path)) as connection:
        actual_cutoff = cutoff or default_cutoff(connection)
    rows, metadata = evaluate(db_path, actual_cutoff, seed)
    overall, deltas = _summary(rows, seed)
    _write_csv(out_dir / "eval_results.csv", rows)
    _write_markdown(out_dir / "baseline_table.md", metadata, overall, deltas)
    _dashboard(out_dir / "dashboard.html", metadata, overall, deltas, rows)
    return rows, metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--cutoff", type=parse_cutoff)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    rows, metadata = run_evaluation(args.db, args.out, args.cutoff, args.seed)
    print(
        f"Evaluated {metadata['n_users']} users at {metadata['cutoff']}; "
        f"wrote {len(rows)} user-strategy rows to {args.out}."
    )


if __name__ == "__main__":
    main()
