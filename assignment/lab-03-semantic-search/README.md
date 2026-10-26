# Lab 03: Semantic Search

Use a pretrained sentence encoder to embed 1,200 synthetic posts, then implement cosine similarity and deterministic top-*k* selection with NumPy. The completed notebook includes executable acceptance checks and a results summary.

## Requirements

- Python 3.11 or newer
- CPU only; a GPU is not required
- Network access on first run to download the pretrained model from Hugging Face

From this directory, install the notebook dependencies and launch Jupyter:

```bash
python -m pip install numpy sentence-transformers jupyter
python -m jupyter notebook starter.ipynb
```

Run the notebook cells from top to bottom. The model is `sentence-transformers/all-MiniLM-L6-v2`, explicitly loaded with `device="cpu"`. The first model load can take a few minutes; it is cached for later runs.

The acceptance cell asserts cosine values, zero-vector handling, tie ordering by ascending `post_id`, top-*k* limits, embedding dimensions, and sorted search output. A successful run prints `All acceptance checks passed` and the sample query's actual top five results.

## References

- [Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- [NumPy quickstart](https://numpy.org/doc/stable/user/quickstart.html)