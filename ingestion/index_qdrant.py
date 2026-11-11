#!/usr/bin/env python3
"""
SchemeSathi - Qdrant Vector Database Indexer
Indexes dense vectors and scheme metadata payloads into local persistent Qdrant
using deterministic UUIDs derived from scheme slugs to ensure idempotent upserts.
"""

import os
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env", override=True)

DEFAULT_LOCAL_PATH = PROJECT_ROOT / "qdrant_storage"
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "schemes")
VECTOR_DIM = 384  # Matches all-MiniLM-L6-v2

def get_qdrant_client(local_path: Path = DEFAULT_LOCAL_PATH) -> QdrantClient:
    """Connect to Qdrant (local persistent embedded storage or cloud)."""
    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "").strip()
    
    if qdrant_url:
        if not qdrant_api_key or "PASTE_YOUR_COPIED" in qdrant_api_key:
            raise ValueError(
                "❌ QDRANT_URL is set, but QDRANT_API_KEY is missing or has the placeholder value in .env!\n"
                "Please open SchemeSathi/.env and paste your copied API Key from the Qdrant Cloud dashboard."
            )
        # Normalize cloud URL (Qdrant cloud uses standard HTTPS port 443)
        clean_url = qdrant_url.rstrip("/")
        if clean_url.endswith(":6333") and "cloud.qdrant.io" in clean_url:
            clean_url = clean_url[:-5]
            
        logger.info(f"Connecting to remote Qdrant at {clean_url} (timeout=60s)...")
        return QdrantClient(url=clean_url, api_key=qdrant_api_key, timeout=60.0, check_compatibility=False)
    else:
        local_path.mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(local_path))

def slug_to_uuid(slug: str) -> str:
    """Deterministic UUID from slug to ensure idempotent upsert."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, slug.strip().lower()))

def init_collection(client: QdrantClient, collection_name: str = COLLECTION_NAME, recreate: bool = False):
    """Ensures collection exists with proper vector dimension and cosine metric."""
    collections = [c.name for c in client.get_collections().collections]
    
    if recreate and collection_name in collections:
        logger.warning(f"Recreating Qdrant collection '{collection_name}'...")
        client.delete_collection(collection_name)
        collections.remove(collection_name)
        
    if collection_name not in collections:
        logger.info(f"Creating Qdrant collection '{collection_name}' (dim={VECTOR_DIM}, metric=Cosine)...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(
                size=VECTOR_DIM,
                distance=qmodels.Distance.COSINE
            )
        )
        logger.success(f"Collection '{collection_name}' created successfully.")
    else:
        logger.info(f"Collection '{collection_name}' already exists.")

def index_schemes_in_qdrant(
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
    client: Optional[QdrantClient] = None,
    collection_name: str = COLLECTION_NAME,
    batch_size: int = 50
):
    """
    Upserts chunk vectors and payload metadata into Qdrant.
    Uses batch_size=50, timeout=60s, wait=False, and retries for network resilience.
    """
    import time

    if client is None:
        client = get_qdrant_client()
        
    init_collection(client, collection_name=collection_name, recreate=False)
    
    total = len(chunks)
    logger.info(f"Indexing {total} schemes into Qdrant collection '{collection_name}' (batch_size={batch_size})...")
    
    for i in tqdm(range(0, total, batch_size), desc="Upserting to Qdrant"):
        batch_chunks = chunks[i:i + batch_size]
        batch_vectors = embeddings[i:i + batch_size]
        
        points = []
        for chunk, vector in zip(batch_chunks, batch_vectors):
            point_id = slug_to_uuid(chunk["id"])
            payload = chunk["payload"].copy()
            payload["chunk_text"] = chunk["text"]
            
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )
            
        # Retry with backoff for transcontinental network stability
        for attempt in range(3):
            try:
                client.upsert(
                    collection_name=collection_name,
                    points=points,
                    wait=False
                )
                break
            except Exception as e:
                if attempt == 2:
                    logger.error(f"Failed to upsert batch {i} after 3 attempts: {e}")
                    raise e
                time.sleep(2)
        
    collection_info = client.get_collection(collection_name)
    logger.success(f"Qdrant indexing complete. Total vectors in collection: {collection_info.points_count}")

if __name__ == "__main__":
    client = get_qdrant_client()
    init_collection(client)
    info = client.get_collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' active. Points: {info.points_count}")

