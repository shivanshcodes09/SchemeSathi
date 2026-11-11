"""
Integration tests for Qdrant dense vector search and BM25 hybrid retrieval.
"""

import pytest
from rag.retrieval import retrieve_schemes, search_bm25
from ingestion.index_qdrant import get_qdrant_client, COLLECTION_NAME

def test_qdrant_collection_exists():
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    assert COLLECTION_NAME in collections
    info = client.get_collection(COLLECTION_NAME)
    assert info.points_count > 4000

def test_bm25_search():
    results = search_bm25("Post-Matric Scholarship", top_k=5)
    assert len(results) > 0
    assert results[0][1] > 0

def test_hybrid_retrieval_profile_filtering():
    profile = {
        "state": "Maharashtra",
        "education": "Graduation / Undergraduate",
        "income": 200000,
        "category": "SC",
        "gender": "all",
        "residence": "both",
        "bpl": False,
        "disability": False
    }
    schemes = retrieve_schemes("scholarship fees reimbursement", profile, top_k=3)
    assert len(schemes) > 0
    for s in schemes:
        # Every scheme must belong to Maharashtra or Central
        assert s["state"] in ["Maharashtra", "Central", "All India"] or s["scope"] == "Central"

