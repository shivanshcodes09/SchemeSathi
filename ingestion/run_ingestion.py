#!/usr/bin/env python3
"""
SchemeSathi - Master Ingestion Runner
Coordinates the full ingestion pipeline:
1. Loads cleaned data
2. Generates semantic chunks
3. Computes vector embeddings (with local caching)
4. Indexes vectors & payloads into local persistent Qdrant
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env", override=True)

from ingestion.clean_data import clean_data, CLEAN_FILE_PATH, RAW_FILE_PATH
from ingestion.chunking import generate_chunks
from ingestion.embeddings import embed_texts, load_embedding_model
from ingestion.index_qdrant import get_qdrant_client, index_schemes_in_qdrant, COLLECTION_NAME
from ingestion.sqlite_index import populate_db

EMBEDDINGS_CACHE_PATH = PROJECT_ROOT / "data" / "processed" / "embeddings.npy"

def run_pipeline(recompute_embeddings: bool = False):
    logger.info("=== Starting SchemeSathi Full Ingestion Pipeline ===")

    # 1. Ensure clean data exists
    if not CLEAN_FILE_PATH.exists():
        logger.info("Clean dataset not found. Running clean_data()...")
        df = clean_data(raw_path=RAW_FILE_PATH, output_path=CLEAN_FILE_PATH)
    else:
        logger.info(f"Loading existing clean data from {CLEAN_FILE_PATH}...")
        df = pd.read_csv(CLEAN_FILE_PATH)

    # 2. Ensure SQLite DB is populated
    populate_db(df)

    # 3. Generate chunks
    chunks = generate_chunks(df)
    texts = [c["text"] for c in chunks]

    # 4. Compute or load embeddings
    if EMBEDDINGS_CACHE_PATH.exists() and not recompute_embeddings:
        logger.info(f"Loading cached embeddings from {EMBEDDINGS_CACHE_PATH}...")
        embeddings_np = np.load(EMBEDDINGS_CACHE_PATH)
        if len(embeddings_np) == len(texts):
            embeddings = embeddings_np.tolist()
            logger.success(f"Loaded {len(embeddings)} cached embeddings.")
        else:
            logger.warning("Cached embeddings length mismatch. Recomputing...")
            embeddings = embed_texts(texts, batch_size=64)
            np.save(EMBEDDINGS_CACHE_PATH, np.array(embeddings, dtype=np.float32))
    else:
        logger.info(f"Computing embeddings for {len(texts)} scheme chunks using all-MiniLM-L6-v2...")
        embeddings = embed_texts(texts, batch_size=64)
        np.save(EMBEDDINGS_CACHE_PATH, np.array(embeddings, dtype=np.float32))
        logger.success(f"Saved embeddings cache to {EMBEDDINGS_CACHE_PATH}.")

    # 5. Index in Qdrant
    client = get_qdrant_client()
    index_schemes_in_qdrant(chunks, embeddings, client=client, collection_name=COLLECTION_NAME)

    logger.success("=== SchemeSathi Ingestion Pipeline Finished Successfully ===")

if __name__ == "__main__":
    force_embed = "--recompute" in sys.argv
    run_pipeline(recompute_embeddings=force_embed)

