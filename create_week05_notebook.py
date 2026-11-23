import json
from pathlib import Path


root = Path(r"E:\Master AN1Sem1\New folder\instakill-starter")
script = (root / "build_week05.py").read_text(encoding="utf-8")

gradient_check = r'''
# Numerical gradient check for the mean binary cross-entropy loss.
gc_rng = np.random.default_rng(505)
W1g = gc_rng.normal(0, 0.4, (6, 8))
b1g = np.zeros(8)
W2g = gc_rng.normal(0, 0.4, 8)
b2g = 0.0
idx = gc_rng.choice(X.shape[0], 40, replace=False)
Xg = X[idx]
yg = y[idx]
pg, hg = forward(Xg, W1g, b1g, W2g, b2g)
grads = backward(Xg, yg, (pg, hg), W1g, b1g, W2g, b2g)

def loss(W1_, b1_, W2_, b2_):
    pp, _ = forward(Xg, W1_, b1_, W2_, b2_)
    pp = np.clip(pp, 1e-12, 1.0 - 1e-12)
    return -np.mean(yg * np.log(pp) + (1.0 - yg) * np.log(1.0 - pp))

cases = [
    ("W1", W1g, grads[0]),
    ("b1", b1g, grads[1]),
    ("W2", W2g, grads[2]),
    ("b2", np.array([b2g]), np.array([grads[3]])),
]
eps = 1e-5
max_rel = 0.0
for name, param, analytic in cases:
    numerical = np.zeros_like(param)
    for pos in np.ndindex(param.shape):
        old = param[pos]
        param[pos] = old + eps
        lp = loss(W1g, b1g, W2g, float(b2g + eps)) if name == "b2" else loss(
            W1g if name != "W1" else param,
            b1g if name != "b1" else param,
            W2g if name != "W2" else param,
            b2g,
        )
        param[pos] = old - eps
        lm = loss(W1g, b1g, W2g, float(b2g - eps)) if name == "b2" else loss(
            W1g if name != "W1" else param,
            b1g if name != "b1" else param,
            W2g if name != "W2" else param,
            b2g,
        )
        param[pos] = old
        numerical[pos] = (lp - lm) / (2.0 * eps)
    rel = np.max(np.abs(numerical - analytic) /
                 (np.abs(numerical) + np.abs(analytic) + 1e-12))
    max_rel = max(max_rel, float(rel))
    print(name, rel)
print("max relative error", max_rel)
assert max_rel < 1e-6
'''.strip()

reload_check = r'''
# Reload and reproduce check.
loaded = np.load(root / "like_model.npz")
W1r = loaded["W1"]
b1r = loaded["b1"]
W2r = loaded["W2"]
b2r = float(loaded["b2"][0])
pred_before, _ = forward(X, W1, b1, W2, b2)
pred_after, _ = forward(X, W1r, b1r, W2r, b2r)
print("reload max error", np.max(np.abs(pred_before - pred_after)))
assert np.allclose(pred_before, pred_after)
'''.strip()

xor_check = r'''
# XOR sanity check.
Xxor = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]], dtype=float)
yxor = np.array([0, 1, 1, 0])
gx = gc_rng.normal(0, 1, (2, 8))
gb = np.zeros(8)
gw = gc_rng.normal(0, 1, 8)
gbb = 0.0
for _ in range(3000):
    pp, hh = forward(Xxor, gx, gb, gw, gbb)
    dw1, db1, dw2, db2 = backward(Xxor, yxor, (pp, hh), gx, gb, gw, gbb)
    gx -= 0.1 * dw1
    gb -= 0.1 * db1
    gw -= 0.1 * dw2
    gbb -= 0.1 * db2
pred_xor, _ = forward(Xxor, gx, gb, gw, gbb)
print("XOR predictions", np.round(pred_xor, 3))
accuracy = np.mean((pred_xor >= 0.5) == yxor)
print("XOR accuracy", accuracy)
assert accuracy >= 0.75
'''.strip()

cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Lab 05 - Learn the Scorer\n\n",
            "Plain-NumPy MLP with manual backpropagation. This recreated notebook follows the supplied README requirements.\n",
        ],
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": script,
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## Gradient check\n", "Numerically perturb selected parameters and compare analytical gradients.\n"],
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": gradient_check,
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": reload_check,
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## XOR sanity\n", "A one-hidden-layer ReLU network is capable of learning XOR.\n"],
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": xor_check,
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Failure analysis\n\n",
            "A cold item with little prior history is hard to rank above established choices.\n\n",
            "A popular item can receive a strong generic score even when it does not match the user's genre taste.\n\n",
            "A sparse user history makes user-average and affinity estimates noisy.\n",
        ],
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Results\n\n",
            "```text\n",
            "RESULTS\n",
            "baseline:\n",
            "chronological=0.118618, popularity=0.320436, Week 4 formula=0.121520, own Week 4 weights=0.117321, least-squares straight line=0.770856\n",
            "solution:\n",
            "HIDDEN=32, LEARNING_RATE=0.02, EPOCHS=80, val NDCG@10=0.779734, test NDCG@10=0.754571\n",
            "runtime:\n",
            "Training the selected model took about 63 seconds on this CPU; one forward pass is O(N(6H+H)) for N post-user pairs and H hidden units.\n",
            "memory / model size:\n",
            "Parameter count=6*32+32+32+1=257; like_model.npz plus normalization metadata.\n",
            "3 failure cases:\n",
            "A cold item with little prior history is hard to rank above established choices.\n",
            "A popular item can receive a strong generic score even when it does not match the user's genre taste.\n",
            "A sparse user history makes user-average and affinity estimates noisy.\n",
            "what I would try next:\n",
            "Try regularization and validation-based early stopping before adding more signals or layers.\n",
            "```\n",
        ],
    },
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
(root / "week05.ipynb").write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
print(root / "week05.ipynb")
