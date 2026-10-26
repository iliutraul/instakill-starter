# Week 3 Assignment Package

This package contains the semantic-search lab and the InstaKill Week 3 endpoint work.

- [Semantic search lab](lab-03-semantic-search/README.md)
- [InstaKill search API and startup behavior](../README.md)
- [Implemented API contract](../docs/api-contract.md)

The lab uses a local pretrained encoder and NumPy retrieval on CPU. InstaKill uses the seeded SQLite posts and a startup-built in-memory index. No vector database or hosted inference service is used.

## References

- [Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- [NumPy quickstart](https://numpy.org/doc/stable/user/quickstart.html)
- [FastAPI path and query parameters](https://fastapi.tiangolo.com/tutorial/path-params/)