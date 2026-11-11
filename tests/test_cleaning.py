"""
Unit tests for data cleaning, state normalization, and education extraction.
"""

import pytest
from ingestion.clean_data import (
    normalize_state,
    extract_education_levels,
    normalize_caste_list,
    calculate_confidence
)

def test_state_normalization():
    assert normalize_state("Delhi (NCT)") == "Delhi"
    assert normalize_state("jammu & kashmir") == "Jammu and Kashmir"
    assert normalize_state("Orissa") == "Odisha"
    assert normalize_state("Pondicherry") == "Puducherry"
    assert normalize_state("All India") == "Central"
    assert normalize_state("Central") == "Central"
    assert normalize_state("Maharashtra") == "Maharashtra"

def test_education_extraction():
    text1 = "Scholarship for class 10 and matric passed students"
    levels1 = extract_education_levels(text1)
    assert "10th Pass / Secondary" in levels1

    text2 = "For undergraduate B.Tech and MBBS degree students"
    levels2 = extract_education_levels(text2)
    assert "Graduation / Undergraduate" in levels2

    text3 = "Fellowship for research scholars pursuing PhD degree"
    levels3 = extract_education_levels(text3)
    assert "PhD / Research" in levels3

def test_caste_normalization():
    assert "SC" in normalize_caste_list("['SC', 'ST']")
    assert "OBC" in normalize_caste_list(["OBC", "General"])
    assert "General" in normalize_caste_list(None)

def test_confidence_scoring():
    import pandas as pd
    high_row = pd.Series({
        "name": "PM-YASASVI",
        "benefits": "Tuition coverage up to 1.25L",
        "eligibility_text": "Students belonging to OBC/EWS category with family income <= 2.5L",
        "documents_required": "Income certificate, Aadhaar",
        "official_url": "https://myscheme.gov.in/schemes/pm-yasasvi",
        "apply_url": "https://yet.nta.ac.in",
        "eligibility_income_max": 250000
    })
    assert calculate_confidence(high_row) == "High"

