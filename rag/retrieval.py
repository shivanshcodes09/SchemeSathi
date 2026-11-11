#!/usr/bin/env python3
"""
SchemeSathi - Hybrid Retrieval Engine
Combines:
1. SQLite demographic pre-filtering (hard criteria)
2. Qdrant dense vector semantic search (Sentence Transformers)
3. BM25 lexical keyword search (exact scheme names and acronyms)
4. Reciprocal Rank Fusion (RRF)
5. Explainable eligibility validation
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import numpy as np
from loguru import logger
from rank_bm25 import BM25Okapi

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env", override=True)

from ingestion.embeddings import embed_query
from ingestion.index_qdrant import get_qdrant_client, COLLECTION_NAME, slug_to_uuid
from ingestion.sqlite_index import query_eligible_slugs, get_scheme_by_slug
from eligibility.matching import filter_schemes_by_eligibility

# In-memory BM25 index cache
_BM25_INDEX = None
_BM25_SLUGS = []
_BM25_CORPUS = []

def get_bm25_index():
    """Initializes or returns cached BM25 index over all cleaned schemes."""
    global _BM25_INDEX, _BM25_SLUGS, _BM25_CORPUS
    if _BM25_INDEX is None:
        import pandas as pd
        from ingestion.clean_data import CLEAN_FILE_PATH
        if CLEAN_FILE_PATH.exists():
            df = pd.read_csv(CLEAN_FILE_PATH)
            _BM25_SLUGS = df["slug"].astype(str).tolist()
            tokenized_corpus = []
            for _, r in df.iterrows():
                text = f"{r.get('name', '')} {r.get('category', '')} {r.get('description', '')}".lower()
                tokens = text.split()
                tokenized_corpus.append(tokens)
            _BM25_CORPUS = tokenized_corpus
            _BM25_INDEX = BM25Okapi(tokenized_corpus)
            logger.info(f"Initialized BM25 index with {len(_BM25_SLUGS)} schemes.")
    return _BM25_INDEX, _BM25_SLUGS

def search_bm25(query: str, candidate_slugs: Optional[set] = None, top_k: int = 30) -> List[tuple]:
    """Runs BM25 search, optionally constrained to candidate slugs."""
    bm25, slugs = get_bm25_index()
    if bm25 is None or not slugs:
        return []
        
    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)
    
    ranked_indices = np.argsort(scores)[::-1]
    results = []
    
    for idx in ranked_indices:
        score = scores[idx]
        if score <= 0.01:
            break
        slug = slugs[idx]
        if candidate_slugs is not None and slug not in candidate_slugs:
            continue
        results.append((slug, float(score)))
        if len(results) >= top_k:
            break
            
    return results

def retrieve_schemes(
    query: str,
    profile: Dict[str, Any],
    top_k: int = 8,
    use_hybrid: bool = True
) -> List[Dict[str, Any]]:
    """
    Main RAG retrieval function:
    1. Pre-filters by profile using SQLite
    2. Runs Qdrant semantic search via query_points
    3. Runs BM25 lexical search (if hybrid enabled)
    4. Merges via Reciprocal Rank Fusion (RRF)
    5. Validates eligibility
    6. Returns top-K schemes
    """
    # 1. Demographic Pre-Filtering via SQLite
    candidate_slugs = query_eligible_slugs(profile)
    if candidate_slugs is not None:
        if len(candidate_slugs) == 0:
            logger.info("User Profile pre-filter identified 0 eligible candidate schemes.")
            return []
        candidate_set = set(candidate_slugs)
        logger.info(f"User Profile pre-filter identified {len(candidate_slugs)} eligible candidate schemes.")
    else:
        candidate_set = None
        logger.info("User Profile pre-filter skipped (database unavailable).")
    
    # 2. Dense Semantic Search via Qdrant
    query_vector = embed_query(query)
    client = get_qdrant_client()
    
    dense_results = []
    try:
        # Search Qdrant using modern query_points API
        search_res = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=150
        )
        for hit in search_res.points:
            slug = hit.payload.get("slug")
            # If candidate set exists, enforce membership
            if candidate_set is not None and slug not in candidate_set:
                continue
            dense_results.append((slug, hit.score, hit.payload))
    except Exception as e:
        logger.error(f"Qdrant query_points error: {e}")
        # Fallback to SQLite records if Qdrant call encounters issues
        fallback_slugs = candidate_slugs[:top_k] if candidate_slugs else []
        for s in fallback_slugs:
            rec = get_scheme_by_slug(s)
            if rec:
                dense_results.append((s, 0.5, rec))

    # 3. Hybrid Lexical Search (BM25)
    rrf_scores = {}
    scheme_payloads = {}
    
    # Add dense ranks to RRF
    for rank, (slug, score, payload) in enumerate(dense_results):
        scheme_payloads[slug] = payload
        rrf_scores[slug] = rrf_scores.get(slug, 0.0) + (1.0 / (60.0 + rank + 1))
        
    if use_hybrid and query.strip():
        bm25_res = search_bm25(query, candidate_slugs=candidate_set, top_k=30)
        for rank, (slug, score) in enumerate(bm25_res):
            if slug not in scheme_payloads:
                rec = get_scheme_by_slug(slug)
                if rec:
                    scheme_payloads[slug] = rec
            rrf_scores[slug] = rrf_scores.get(slug, 0.0) + (1.0 / (60.0 + rank + 1))

    # Sort candidates by combined RRF score
    sorted_slugs = sorted(rrf_scores.keys(), key=lambda s: rrf_scores[s], reverse=True)
    
    candidate_schemes = []
    for slug in sorted_slugs:
        if slug in scheme_payloads:
            item = scheme_payloads[slug].copy()
            item["retrieval_score"] = rrf_scores[slug]
            candidate_schemes.append(item)

    # 4. Final Rule-Based Eligibility Check
    validated_schemes = filter_schemes_by_eligibility(candidate_schemes, profile)
    
    # Return top_k
    final_schemes = validated_schemes[:top_k]
    logger.info(f"Retrieved and validated {len(final_schemes)} schemes for query.")
    return final_schemes

if __name__ == "__main__":
    profile = {
        "state": "Maharashtra",
        "education": "Graduation / Undergraduate",
        "income": 200000,
        "category": "SC",
        "gender": "female",
        "residence": "urban",
        "bpl": False,
        "disability": False
    }
    results = retrieve_schemes("scholarship for higher education college fees", profile, top_k=3)
    for r in results:
        print(f"- {r.get('name')} (Score: {r.get('retrieval_score', 0):.4f})")
