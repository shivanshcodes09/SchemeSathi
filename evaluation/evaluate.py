#!/usr/bin/env python3
"""
SchemeSathi - Rigorous Empirical Evaluation Engine
Evaluates retrieval relevance, eligibility compliance, citation integrity,
and state scope adherence across 32 real-world test cases.
Never fabricates performance metrics - computes real metrics on retrieved output.
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
from loguru import logger
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env", override=True)

from rag.retrieval import retrieve_schemes
from eligibility.matching import evaluate_scheme_eligibility

TEST_QUESTIONS_PATH = PROJECT_ROOT / "evaluation" / "test_questions.json"
RESULTS_PATH = PROJECT_ROOT / "evaluation" / "evaluation_results.json"

def run_evaluation() -> Dict[str, Any]:
    with open(TEST_QUESTIONS_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    logger.info(f"Starting evaluation across {len(test_cases)} test questions...")
    
    total_queries = len(test_cases)
    relevance_scores = []
    eligibility_accuracy_list = []
    citation_accuracy_list = []
    state_precision_list = []
    latencies = []
    detailed_results = []

    for idx, tc in enumerate(test_cases, 1):
        q_id = tc["id"]
        question = tc["question"]
        profile = tc["profile"]
        expected_keywords = tc.get("expected_keywords", [])
        
        t0 = time.time()
        retrieved = retrieve_schemes(question, profile, top_k=5, use_hybrid=True)
        latency = (time.time() - t0) * 1000.0
        latencies.append(latency)

        if not retrieved:
            logger.warning(f"[{q_id}] No schemes retrieved.")
            relevance_scores.append(0.0)
            eligibility_accuracy_list.append(1.0)
            citation_accuracy_list.append(1.0)
            state_precision_list.append(1.0)
            detailed_results.append({
                "id": q_id,
                "question": question,
                "retrieved_count": 0,
                "latency_ms": latency,
                "relevance_hit": False,
                "eligibility_rate": 1.0,
                "citation_rate": 1.0
            })
            continue

        # 1. Relevance: check if any retrieved scheme contains expected keywords in name, desc, benefits, or eligibility
        has_relevant_hit = False
        for s in retrieved:
            full_text = f"{s.get('name', '')} {s.get('category', '')} {s.get('description', '')} {s.get('benefits', '')} {s.get('eligibility_summary', '')}".lower()
            if any(kw.lower() in full_text for kw in expected_keywords):
                has_relevant_hit = True
                break
        relevance_scores.append(1.0 if has_relevant_hit else 0.0)

        # 2. Eligibility Adherence: test every returned scheme with matching rule engine
        elig_hits = 0
        cit_hits = 0
        state_valid_hits = 0
        
        user_state = profile.get("state", "All India")
        for s in retrieved:
            is_ok, matches, mismatches = evaluate_scheme_eligibility(s, profile)
            if is_ok:
                elig_hits += 1
                
            # Citation check: official_url or apply_url present
            off_url = str(s.get("official_url", "")).strip()
            app_url = str(s.get("apply_url", "")).strip()
            if (off_url and off_url.startswith("http")) or (app_url and app_url.startswith("http")):
                cit_hits += 1

            # State precision: must be user_state or Central
            s_state = s.get("state", "Central")
            s_scope = s.get("scope", "Central")
            if user_state in ["All India", "All", "Central"] or s_scope == "Central" or s_state == "Central" or s_state.lower() == user_state.lower():
                state_valid_hits += 1

        elig_rate = elig_hits / len(retrieved)
        cit_rate = cit_hits / len(retrieved)
        state_prec = state_valid_hits / len(retrieved)

        eligibility_accuracy_list.append(elig_rate)
        citation_accuracy_list.append(cit_rate)
        state_precision_list.append(state_prec)

        detailed_results.append({
            "id": q_id,
            "question": question,
            "retrieved_count": len(retrieved),
            "top_scheme": retrieved[0].get("name") if retrieved else None,
            "latency_ms": round(latency, 1),
            "relevance_hit": has_relevant_hit,
            "eligibility_rate": round(elig_rate, 3),
            "citation_rate": round(cit_rate, 3),
            "state_precision": round(state_prec, 3)
        })

    # Summary Metrics
    avg_relevance = float(np.mean(relevance_scores)) * 100.0
    avg_eligibility = float(np.mean(eligibility_accuracy_list)) * 100.0
    avg_citation = float(np.mean(citation_accuracy_list)) * 100.0
    avg_state_prec = float(np.mean(state_precision_list)) * 100.0
    avg_latency = float(np.mean(latencies))

    summary = {
        "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_test_questions": total_queries,
        "metrics": {
            "retrieval_relevance_rate_pct": round(avg_relevance, 2),
            "eligibility_matching_accuracy_pct": round(avg_eligibility, 2),
            "official_citation_rate_pct": round(avg_citation, 2),
            "state_scope_precision_pct": round(avg_state_prec, 2),
            "mean_retrieval_latency_ms": round(avg_latency, 1)
        },
        "detailed_results": detailed_results
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 65)
    print(" SchemeSathi - Rigorous Empirical Evaluation Results")
    print("=" * 65)
    print(f"Total Test Questions Evaluated : {total_queries}")
    print(f"Retrieval Relevance (Hit@5)   : {avg_relevance:.1f}%")
    print(f"Eligibility Rule Compliance   : {avg_eligibility:.1f}%")
    print(f"Official Citation Integrity    : {avg_citation:.1f}%")
    print(f"State Scope Filtering Precision: {avg_state_prec:.1f}%")
    print(f"Mean Query Retrieval Latency   : {avg_latency:.1f} ms")
    print("=" * 65)
    print(f"Detailed results saved to: {RESULTS_PATH}\n")

    return summary

if __name__ == "__main__":
    run_evaluation()

