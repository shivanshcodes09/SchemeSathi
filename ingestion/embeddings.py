#!/usr/bin/env python3
"""
SchemeSathi - Sentence Transformers Embedding Pipeline
Generates dense vector embeddings using all-MiniLM-L6-v2 (or configured model)
leveraging Apple Silicon MPS hardware acceleration where available.
"""

import os
from typing import List, Union
import torch
from sentence_transformers import SentenceTransformer
from loguru import logger
from tqdm import tqdm

DEFAULT_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_MODEL_INSTANCE = None

def get_device() -> str:
    """Detect fastest available torch device (mps for Apple Silicon, else cpu)."""
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    return "cpu"

def load_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    """Loads and caches the SentenceTransformer model instance."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        device = get_device()
        logger.info(f"Loading embedding model '{model_name}' on device '{device}'...")
        try:
            # Try offline / local files first to prevent huggingface_hub network timeouts
            _MODEL_INSTANCE = SentenceTransformer(model_name, device=device, local_files_only=True)
        except Exception:
            _MODEL_INSTANCE = SentenceTransformer(model_name, device=device)
        logger.success(f"Embedding model loaded successfully (dim={_MODEL_INSTANCE.get_sentence_embedding_dimension()}).")
    return _MODEL_INSTANCE

def embed_texts(texts: List[str], batch_size: int = 64, show_progress: bool = True) -> List[List[float]]:
    """Encodes a list of strings into dense normalized vector embeddings."""
    model = load_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        normalize_embeddings=True,
        convert_to_numpy=True
    )
    return embeddings.tolist()

def embed_query(query: str) -> List[float]:
    """Encodes a single user query into a normalized vector."""
    model = load_embedding_model()
    embedding = model.encode(
        query,
        normalize_embeddings=True,
        convert_to_numpy=True
    )
    return embedding.tolist()

if __name__ == "__main__":
    test_texts = [
        "Post-Matric Scholarship for SC Students in Maharashtra",
        "PM-Yasasvi scheme for OBC and EWS students"
    ]
    vectors = embed_texts(test_texts, show_progress=False)
    print(f"Generated {len(vectors)} vectors with dimension {len(vectors[0])}.")

