"""
Unit tests for deterministic eligibility rules matching engine.
"""

import pytest
from eligibility.matching import evaluate_scheme_eligibility, filter_schemes_by_eligibility

def test_income_limit_compliance():
    scheme_with_cap = {
        "name": "PM Yasasvi",
        "state": "Central",
        "scope": "Central",
        "income_max": 250000,
        "caste": ["OBC", "EWS"],
        "gender": "all",
        "bpl_required": False,
        "disability_required": False
    }

    # Within income
    profile_pass = {"state": "Punjab", "income": 200000, "category": "OBC"}
    ok, matches, mismatches = evaluate_scheme_eligibility(scheme_with_cap, profile_pass)
    assert ok is True
    assert len(mismatches) == 0

    # Exceeding income
    profile_fail = {"state": "Punjab", "income": 400000, "category": "OBC"}
    ok, matches, mismatches = evaluate_scheme_eligibility(scheme_with_cap, profile_fail)
    assert ok is False
    assert any("exceeds the maximum" in m for m in mismatches)

def test_state_domicile_protection():
    rajasthan_scheme = {
        "name": "Rajasthan Tribal Scholarship",
        "state": "Rajasthan",
        "scope": "State",
        "income_max": None,
        "caste": ["ST"],
        "gender": "all",
        "bpl_required": False,
        "disability_required": False
    }

    # Domicile match
    profile_rj = {"state": "Rajasthan", "category": "ST"}
    ok, _, _ = evaluate_scheme_eligibility(rajasthan_scheme, profile_rj)
    assert ok is True

    # Domicile mismatch
    profile_mh = {"state": "Maharashtra", "category": "ST"}
    ok, _, mismatches = evaluate_scheme_eligibility(rajasthan_scheme, profile_mh)
    assert ok is False
    assert any("Rajasthan" in m for m in mismatches)

def test_disability_and_bpl_filters():
    disability_scheme = {
        "name": "Scholarship for Students with Disabilities",
        "state": "Central",
        "scope": "Central",
        "income_max": None,
        "caste": ["All"],
        "gender": "all",
        "bpl_required": False,
        "disability_required": True
    }

    # Non-disabled user
    p1 = {"state": "Delhi", "disability": False}
    ok1, _, mismatches1 = evaluate_scheme_eligibility(disability_scheme, p1)
    assert ok1 is False

    # Disabled user
    p2 = {"state": "Delhi", "disability": True}
    ok2, _, _ = evaluate_scheme_eligibility(disability_scheme, p2)
    assert ok2 is True

