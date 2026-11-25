import csv
import json
import math
import random
import time
import zipfile
from pathlib import Path

import numpy as np


ROOT = Path(r"E:\Master AN1Sem1\New folder\instakill-starter")
DATA = ROOT / "ml-latest-small" / "ml-latest-small"
SEED = 505
rng = np.random.default_rng(SEED)
random.seed(SEED)


def read_ratings():
    rows = []
    with open(DATA / "ratings.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((int(r["userId"]), int(r["movieId"]), float(r["rating"]), int(r["timestamp"])))
    return sorted(rows, key=lambda r: r[3])


def read_movies():
    movies = {}
    with open(DATA / "movies.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            movies[int(r["movieId"])] = set(r["genres"].split("|"))
    return movies


ratings = read_ratings()
genres = read_movies()
all_items = sorted(genres)
item_created = {}
for _, iid, _, ts in ratings:
    item_created[iid] = min(ts, item_created.get(iid, ts))

from bisect import bisect_left

user_history = {}
item_history = {}
for uid, iid, rating, ts in ratings:
    user_history.setdefault(uid, []).append((ts, iid, rating))
    item_history.setdefault(iid, []).append((ts, uid, rating))
for uid in user_history:
    user_history[uid].sort()
for iid in item_history:
    item_history[iid].sort()

user_times = {uid: [row[0] for row in rows] for uid, rows in user_history.items()}
item_times = {iid: [row[0] for row in rows] for iid, rows in item_history.items()}

live_cache = {}

timestamps = np.array([r[3] for r in ratings])
like_rows = [r for r in ratings if r[2] >= 4.0]
t70 = float(np.quantile(np.array([r[3] for r in like_rows]), 0.70))
t85 = float(np.quantile(np.array([r[3] for r in like_rows]), 0.85))
train_likes = [r for r in like_rows if r[3] <= t70]
val_likes = [r for r in like_rows if t70 < r[3] <= t85]
test_likes = [r for r in like_rows if r[3] > t85]


def live_signals(uid, iid, ts):
    key = (uid, iid, ts)
    if key in live_cache:
        return live_cache[key]
    uhist = user_history.get(uid, [])
    ihist = item_history.get(iid, [])
    utimes = user_times.get(uid, [])
    itimes = item_times.get(iid, [])
    uparts = uhist[:bisect_left(utimes, ts + 1)]
    iparts = ihist[:bisect_left(itimes, ts + 1)]
    uvals = [row[2] for row in uparts]
    ivals = [row[2] for row in iparts]
    icount = len(ivals)
    ucount = len(uvals)

    uitems = {row[1]: row[2] for row in uparts}
    same_genre_count = 0
    target_genres = genres.get(iid, set())
    for oid in uitems:
        if target_genres & genres.get(oid, set()):
            same_genre_count += 1
    genre_affinity = 3.5 + 0.3 * same_genre_count / max(1, len(uitems))

    freshness = 1.0 - min(1.0, max(0.0, (ts - item_created[iid]) / (365.25 * 24 * 3600 * 6)))
    pop_normalized = icount / 500.0
    user_avg = np.mean(uvals) if uvals else 3.5
    item_avg = np.mean(ivals) if ivals else 3.5
    novel = 1.0 if iid not in uitems else 0.0
    result = np.array([
        freshness,
        pop_normalized,
        (user_avg - 3.5) / 1.5,
        (item_avg - 3.5) / 1.5,
        (genre_affinity - 3.5) / 1.5,
        novel,
    ], dtype=np.float64)
    live_cache[key] = result
    return result


def make_training(likes):
    X, y = [], []
    for uid, iid, rating, ts in likes:
        X.append(live_signals(uid, iid, ts))
        y.append(1.0)
        eligible = [x for x in all_items if item_created.get(x, ts + 1) <= ts and x != iid]
        negatives = rng.choice(eligible, size=1, replace=False)
        for neg in negatives:
            X.append(live_signals(uid, int(neg), ts))
            y.append(0.0)
    X = np.asarray(X)
    y = np.asarray(y)
    Xmean = X.mean(axis=0)
    Xstd = X.std(axis=0)
    Xstd[Xstd == 0] = 1.0
    return X, y, Xmean, Xstd


Xraw, y, Xmean, Xstd = make_training(train_likes)
X = (Xraw - Xmean) / Xstd


def sigmoid(z):
    z = np.clip(z, -40, 40)
    return 1.0 / (1.0 + np.exp(-z))


def forward(X, W1, b1, W2, b2):
    z1 = X @ W1 + b1
    h = np.maximum(z1, 0)
    z2 = h @ W2 + b2
    return sigmoid(z2), h


def backward(X, y, cache, W1, b1, W2, b2):
    prob, h = cache
    n = X.shape[0]
    dz2 = (prob - y)[:, None] / n
    dW2 = h.T @ dz2
    db2 = dz2.sum(axis=0)
    dh = dz2 @ W2[None, :]
    dz1 = dh * (h > 0)
    dW1 = X.T @ dz1
    db1 = dz1.sum(axis=0)
    return dW1, db1, dW2[:, 0], float(db2[0])


def train_network(hidden, lr, epochs):
    W1 = rng.normal(0, 0.4, (6, hidden))
    b1 = np.zeros(hidden)
    W2 = rng.normal(0, 0.4, hidden)
    b2 = 0.0
    order = np.arange(X.shape[0])
    batch = 256
    for epoch in range(epochs):
        rng.shuffle(order)
        for start in range(0, len(order), batch):
            idx = order[start:start + batch]
            prob, h = forward(X[idx], W1, b1, W2, b2)
            cache = (prob, h)
            dW1, db1, dW2, db2 = backward(X[idx], y[idx], cache, W1, b1, W2, b2)
            W1 -= lr * dW1
            b1 -= lr * db1
            W2 -= lr * dW2
            b2 -= lr * db2
    return W1, b1, W2, b2


def ndcg(scores, relevant_indices):
    order = np.argsort(-scores)
    dcg = 0.0
    for rank, idx in enumerate(order[:10], start=1):
        if idx in relevant_indices:
            dcg += 1.0 / math.log2(rank + 1)
    return dcg


def exam(likes, model=None):
    if model is not None:
        W1, b1, W2, b2 = model
    vals = []
    for uid, iid, _, ts in likes:
        candidates = [iid]
        eligible = [x for x in all_items if item_created.get(x, ts + 1) <= ts and x != iid]
        candidates += list(random.sample(eligible, min(99, len(eligible))))
        if model is None:
            yield uid, iid, ts, candidates
        else:
            Xcand = np.asarray([(live_signals(uid, x, ts) - Xmean) / Xstd for x in candidates])
            scores, _ = forward(Xcand, W1, b1, W2, b2)
            vals.append(ndcg(scores, {0}))
    if model is not None:
        return float(np.mean(vals))


def model_ndcg(likes, model):
    W1, b1, W2, b2 = model
    vals = []
    for uid, iid, _, ts in likes:
        candidates = [iid]
        eligible = [x for x in all_items if item_created.get(x, ts + 1) <= ts and x != iid]
        candidates += list(random.sample(eligible, min(99, len(eligible))))
        Xcand = np.asarray([(live_signals(uid, x, ts) - Xmean) / Xstd for x in candidates])
        scores, _ = forward(Xcand, W1, b1, W2, b2)
        vals.append(ndcg(scores, {0}))
    return float(np.mean(vals))


def baseline_scores(likes, kind):
    vals = []
    for uid, iid, _, ts in likes:
        candidates = [iid]
        eligible = [x for x in all_items if item_created.get(x, ts + 1) <= ts and x != iid]
        candidates += list(random.sample(eligible, min(99, len(eligible))))
        scores = []
        for x in candidates:
            s = live_signals(uid, x, ts)
            if kind == "chronological":
                score = s[0]
            elif kind == "popularity":
                score = s[1]
            elif kind == "week4":
                score = 0.40 * s[4] + 0.35 * s[0] + 0.25 * s[1]
            elif kind == "own_weights":
                score = 0.20 * s[4] + 0.50 * s[0] + 0.30 * s[1]
            else:
                raise ValueError(kind)
            scores.append(score)
        vals.append(ndcg(np.asarray(scores), {0}))
    return float(np.mean(vals))


# Linear least squares straight-line baseline
A = np.column_stack([X, np.ones(X.shape[0])])
linear_coef = np.linalg.lstsq(A, y, rcond=None)[0]


def linear_ndcg(likes):
    vals = []
    for uid, iid, _, ts in likes:
        candidates = [iid]
        eligible = [x for x in all_items if item_created.get(x, ts + 1) <= ts and x != iid]
        candidates += list(random.sample(eligible, min(99, len(eligible))))
        Xcand = np.asarray([(live_signals(uid, x, ts) - Xmean) / Xstd for x in candidates])
        scores = np.column_stack([Xcand, np.ones(len(Xcand))]) @ linear_coef
        vals.append(ndcg(scores, {0}))
    return float(np.mean(vals))


print("boundaries", t70, t85, flush=True)
print("sizes", len(train_likes), len(val_likes), len(test_likes), flush=True)

baselines = {
    "chronological": baseline_scores(val_likes, "chronological"),
    "popularity": baseline_scores(val_likes, "popularity"),
    "week4": baseline_scores(val_likes, "week4"),
    "own_week4": baseline_scores(val_likes, "own_weights"),
    "linear": linear_ndcg(val_likes),
}
print("baselines val", baselines)

best = None
for hidden in (16, 32):
    for lr in (0.02,):
        for epochs in (80,):
            started = time.perf_counter()
            model = train_network(hidden, lr, epochs)
            score = model_ndcg(val_likes, model)
            elapsed = time.perf_counter() - started
            print("candidate", hidden, lr, epochs, score, elapsed)
            if best is None or score > best[0]:
                best = (score, hidden, lr, epochs, model)

score, hidden, lr, epochs, model = best
print("BEST", best[:4])
test_score = model_ndcg(test_likes, model)
print("TEST_ONE_RUN", test_score)

# Export model and metadata.
W1, b1, W2, b2 = model
np.savez(ROOT / "like_model.npz", W1=W1, b1=b1, W2=W2, b2=np.array([b2]), Xmean=Xmean, Xstd=Xstd)

results = {
    "best_val": score,
    "hidden": hidden,
    "learning_rate": lr,
    "epochs": epochs,
    "test": test_score,
    "baselines_val": baselines,
    "parameter_count": int(W1.size + b1.size + W2.size + 1),
    "model_size": (ROOT / "like_model.npz").stat().st_size,
}
(ROOT / "week05_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
