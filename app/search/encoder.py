"""CPU Sentence Transformers adapter."""

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray


class SentenceTransformerEncoder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name, device="cpu")

    def encode_documents(self, texts: Sequence[str]) -> NDArray[np.float32]:
        embeddings = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)

    def encode_query(self, text: str) -> NDArray[np.float32]:
        embedding = self._model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embedding, dtype=np.float32)