# Offline feed evaluation protocol

**Question.** This replay asks whether chronological, popularity, `for_you`, or `learned` puts posts a user later liked into the first ten positions, how large the difference is from the strongest baseline, which activity groups differ, and how uncertain those estimates are. It evaluates product rankings over the full available post set rather than the lab's one-positive-among-99-random-items task; its NDCG values are not comparable to the lab's.

**Cut-off and snapshot.** Unless `--cutoff` is supplied, `T` is the timestamp at the 80th-percentile position of all positive MovieLens ratings. The evaluator copies SQLite to a temporary database and removes likes and ratings at or after `T`, posts created at or after `T`, and follows; it then derives follows again from only the snapshot's remaining likes. Every call to the shared feed service receives `now=T`.

**Users.** A user is included only with at least three likes before `T` and at least one later like on a post created before `T`. Activity groups are based on the user's pre-cut-off like count: new (<10), casual (10-49), regular (50-199), and power (200+). No user is sampled or dropped after this eligibility check.

**Candidates.** For each eligible user and strategy, `rank_feed` is called for the top ten from the snapshot's posts available before `T`; posts already liked by that user before `T` are excluded. The four strategies are chronological by post creation time, popularity by pre-cut-off rating count, `for_you` using the existing Week 5 genre-affinity/freshness/popularity weights, and `learned` using `like_model.npz`. The offline script does not implement a second copy of these ranking rules.

**Relevance.** A user's relevant set contains each post they liked at or after `T` that exists among the pre-cut-off snapshot candidates. A hit is binary; rating magnitude does not add extra gain.

**Metric.** One NDCG@10 is calculated per user and strategy. DCG is the sum of `1/log2(rank+1)` for relevant returned posts (one-based rank); the ideal DCG places up to ten relevant posts first. Scores are in [0,1], and users with no returned relevant post score zero.

**Intervals and comparisons.** Each strategy's mean and the paired `learned`-minus-best-baseline difference use 5,000 user-level bootstrap resamples with the requested fixed seed; the 2.5th and 97.5th percentiles form the 95% interval. The strongest baseline is selected by observed mean overall and separately within each activity group. A difference is called a win or loss only when its interval is entirely above or below zero; otherwise it is unclear.

**Slices.** Results are reported overall and for the four activity groups defined above. Group-level deltas compare learned with that group's highest-mean baseline; the dashboard also shows each strategy's group mean with its own 95% user bootstrap interval.

**Known limitation - model exposure.** In this seeded run, 470 later likes from the 25 eligible users count toward evaluation: 83 (17.7%) fall between the Week 5 80th-percentile evaluation cut-off and its 85th-percentile validation cut-off, while zero fall in the model's first-70%-of-likes fitting interval. Validation-based model selection can therefore make `learned` optimistic on those 83 labels, although the remaining 387 are beyond that validation period; the observed learned mean is 0.0183 versus 0.1012 for popularity, but this replay cannot estimate how much of that score the overlap contributes.

**Known limitation - population.** This database has 25 eligible MovieLens users and a catalog of older films with activity spanning 1996-2018, not a social network's short-lived posts. In this run, popularity is the strongest baseline in the new, casual, and regular activity groups; the power group has zero scores and is uninformative. Those user-activity slices favor popularity on this catalog, but they do not isolate fresh posts or establish a winner for a real feed; a freshness/chronological strategy could behave differently with posts from the last few days.
