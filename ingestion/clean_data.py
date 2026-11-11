#!/usr/bin/env python3
"""
SchemeSathi - Data Cleaning & Normalization Pipeline
Cleans raw scheme records, normalizes state names, extracts education levels
from unstructured eligibility text, computes confidence scores, and prepares
structured data for exact filtering and Qdrant ingestion.
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Set
import pandas as pd
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILE_PATH = PROJECT_ROOT / "data" / "raw" / "schemes_raw.parquet"
CLEAN_FILE_PATH = PROJECT_ROOT / "data" / "processed" / "schemes_clean.csv"

# Canonical list of 28 Indian States & 8 Union Territories
CANONICAL_STATES = {
    # 28 States
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    # 8 Union Territories
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry"
}

STATE_ALIASES = {
    "all": "Central",
    "central": "Central",
    "pan-india": "Central",
    "all india": "Central",
    "national": "Central",
    "orissa": "Odisha",
    "uttaranchal": "Uttarakhand",
    "pondicherry": "Puducherry",
    "delhi (nct)": "Delhi",
    "nct of delhi": "Delhi",
    "jammu & kashmir": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra & nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "andaman & nicobar": "Andaman and Nicobar Islands",
}

# Regex rules for education level extraction from text
EDUCATION_PATTERNS = {
    "Below 10th": [
        r"\bclass\s*(?:[1-8]|i{1,3}|iv|v|vi|vii|viii)\b",
        r"\bpre[\s-]?matric\b",
        r"\bprimary\b",
        r"\bmiddle\s*school\b",
        r"\belementary\b"
    ],
    "10th Pass / Secondary": [
        r"\bclass\s*(?:9|10|ix|x)\b",
        r"\b10th\s*pass\b",
        r"\bsecondary\b",
        r"\bmatric(?:ulation)?\b",
        r"\bsslc\b",
        r"\bhigh\s*school\b"
    ],
    "12th Pass / Higher Secondary": [
        r"\bclass\s*(?:11|12|xi|xii)\b",
        r"\b12th\s*pass\b",
        r"\bhigher\s*secondary\b",
        r"\bintermediate\b",
        r"\bpuc\b",
        r"\b10\s*\+\s*2\b",
        r"\bsenior\s*secondary\b"
    ],
    "Diploma / Polytechnic": [
        r"\bdiploma\b",
        r"\bpolytechnic\b",
        r"\biti\b",
        r"\bvocational\b"
    ],
    "Graduation / Undergraduate": [
        r"\bunder[\s-]?graduate\b",
        r"\bgraduation\b",
        r"\bgraduate\b",
        r"\bbachelor\b",
        r"\bb\.?\s*tech\b",
        r"\bb\.?\s*e\.?\b",
        r"\bb\.?\s*sc\b",
        r"\bb\.?\s*com\b",
        r"\bb\.?\s*a\.?\b",
        r"\bmbbs\b",
        r"\bbca\b",
        r"\bbba\b",
        r"\bug\s*degree\b",
        r"\bcollege\s*student\b"
    ],
    "Post-Graduation": [
        r"\bpost[\s-]?graduate\b",
        r"\bpost[\s-]?graduation\b",
        r"\bmaster(?:'s)?\b",
        r"\bm\.?\s*tech\b",
        r"\bm\.?\s*sc\b",
        r"\bm\.?\s*com\b",
        r"\bm\.?\s*a\.?\b",
        r"\bmba\b",
        r"\bmca\b",
        r"\bpg\s*degree\b"
    ],
    "PhD / Research": [
        r"\bph\.?\s*d\b",
        r"\bdoctorate\b",
        r"\bresearch\s*scholar\b",
        r"\bm\.?\s*phil\b",
        r"\bfellowship\b",
        r"\bpost[\s-]?doctoral\b"
    ]
}

def normalize_state(val: Optional[str]) -> str:
    """Normalize raw state string to canonical state or Central."""
    if not val or pd.isna(val):
        return "Central"
    val_clean = str(val).strip()
    val_lower = val_clean.lower()
    
    if val_lower in STATE_ALIASES:
        return STATE_ALIASES[val_lower]
    
    for canon in CANONICAL_STATES:
        if canon.lower() == val_lower or canon.lower() in val_lower:
            return canon
            
    return val_clean

def extract_education_levels(text: str) -> List[str]:
    """Parse text and return matched education levels."""
    if not text or pd.isna(text):
        return ["Any Education Level"]
    
    text_lower = str(text).lower()
    matches = []
    for level, patterns in EDUCATION_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                matches.append(level)
                break
                
    if not matches:
        return ["Any Education Level"]
    return matches

def normalize_caste_list(caste_val) -> List[str]:
    """Parse caste field safely into a standardized list of strings."""
    if caste_val is None:
        return ["All", "General"]
    
    if isinstance(caste_val, (list, tuple)):
        items = [str(x).strip(" '\"[]") for x in caste_val if str(x).strip(" '\"[]")]
        return items if items else ["All", "General"]
        
    try:
        if pd.isna(caste_val):
            return ["All", "General"]
    except Exception:
        pass
        
    s = str(caste_val).strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = json.loads(s.replace("'", '"'))
            if isinstance(parsed, list):
                items = [str(x).strip(" '\"[]") for x in parsed if str(x).strip(" '\"[]")]
                return items if items else ["All", "General"]
        except Exception:
            pass
            
    # Comma-separated or simple text
    parts = [p.strip(" '\"[]") for p in s.split(",") if p.strip(" '\"[]")]
    return parts if parts else ["All", "General"]

def calculate_confidence(row: pd.Series) -> str:
    """
    Score data completeness into High (green), Medium (yellow), or Low (red).
    """
    score = 0
    # Key signals
    if pd.notna(row.get("name")) and str(row.get("name")).strip():
        score += 1
    if pd.notna(row.get("benefits")) and str(row.get("benefits")).strip():
        score += 1
    if pd.notna(row.get("eligibility_text")) and len(str(row.get("eligibility_text")).strip()) > 30:
        score += 2
    if pd.notna(row.get("documents_required")) and str(row.get("documents_required")).strip():
        score += 1
    if pd.notna(row.get("official_url")) and str(row.get("official_url")).startswith("http"):
        score += 1
    if pd.notna(row.get("apply_url")) and str(row.get("apply_url")).startswith("http"):
        score += 1
    if pd.notna(row.get("eligibility_income_max")):
        score += 1

    if score >= 6:
        return "High"
    elif score >= 3:
        return "Medium"
    else:
        return "Low"

def clean_data(raw_path: Path = RAW_FILE_PATH, output_path: Path = CLEAN_FILE_PATH) -> pd.DataFrame:
    logger.info(f"Loading raw dataset from {raw_path}...")
    df = pd.read_parquet(raw_path)
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} records.")

    # 1. Deduplicate by slug
    if "slug" in df.columns:
        df = df.drop_duplicates(subset=["slug"], keep="first").copy()
    else:
        # Generate slug if missing
        df["slug"] = df["name"].astype(str).str.lower().str.replace(r"[^\w\s-]", "", regex=True).str.replace(r"\s+", "-", regex=True)
        df = df.drop_duplicates(subset=["slug"], keep="first").copy()

    dedup_count = len(df)
    if initial_count != dedup_count:
        logger.info(f"Deduplication removed {initial_count - dedup_count} duplicates ({dedup_count} remaining).")

    # 2. Normalize State
    df["state_normalized"] = df["state"].apply(normalize_state)
    
    # 3. Determine Scheme Scope: Central vs State
    def determine_scope(row) -> str:
        st = str(row["state_normalized"]).strip().lower()
        if st == "central":
            return "Central"
        # Check eligibility_state list if present
        el_state = row.get("eligibility_state")
        if isinstance(el_state, (list, tuple)) and ("All" in el_state or "all" in el_state):
            return "Central"
        return "State"

    df["scheme_scope"] = df.apply(determine_scope, axis=1)

    # 4. Extract Education Levels from eligibility_text + name + description
    def extract_edu(row) -> List[str]:
        combined = f"{row.get('name', '')} {row.get('eligibility_text', '')} {row.get('description', '')}"
        return extract_education_levels(combined)

    df["education_levels"] = df.apply(extract_edu, axis=1)
    df["education_levels_str"] = df["education_levels"].apply(lambda lst: ", ".join(lst))

    # 5. Clean Income Criteria
    def parse_income(val):
        if pd.isna(val) or val is None:
            return None
        try:
            num = float(val)
            return int(num) if num >= 0 else None
        except (ValueError, TypeError):
            return None

    df["income_max_clean"] = df["eligibility_income_max"].apply(parse_income)
    df["income_limit_specified"] = df["income_max_clean"].notna()

    # 6. Normalize Caste List
    df["caste_list"] = df["eligibility_caste"].apply(normalize_caste_list)
    df["caste_str"] = df["caste_list"].apply(lambda lst: ", ".join(lst))

    # 7. Gender & Residence Normalization
    df["gender_clean"] = df["eligibility_gender"].fillna("all").astype(str).str.lower().str.strip()
    df["gender_clean"] = df["gender_clean"].apply(lambda g: g if g in ["male", "female", "all"] else "all")

    df["residence_clean"] = df["eligibility_residence"].fillna("both").astype(str).str.lower().str.strip()
    df["residence_clean"] = df["residence_clean"].apply(lambda r: r if r in ["rural", "urban", "both"] else "both")

    # 8. BPL & Disability Flags
    df["bpl_required"] = df["eligibility_bpl"].fillna(False).astype(bool)
    df["disability_required"] = df["eligibility_disability"].fillna(False).astype(bool)

    # 9. Clean Text Fields (null safety)
    text_cols = ["name", "description", "ministry", "department", "category", "benefits",
                 "eligibility_text", "application_process", "documents_required", "apply_url", "official_url"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
        else:
            df[col] = ""

    # 10. Data Confidence Score
    df["confidence_score"] = df.apply(calculate_confidence, axis=1)

    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.success(f"Saved cleaned dataset to {output_path} ({len(df)} records).")

    print("\n" + "=" * 60)
    print(" Cleaned Dataset Summary")
    print("=" * 60)
    print(f"Total Clean Records    : {len(df)}")
    print(f"Central Schemes        : {(df['scheme_scope'] == 'Central').sum()}")
    print(f"State Schemes          : {(df['scheme_scope'] == 'State').sum()}")
    print(f"Income Limit Specified : {df['income_limit_specified'].sum()} ({df['income_limit_specified'].mean() * 100:.1f}%)")
    print("\nConfidence Score Distribution:")
    print(df["confidence_score"].value_counts())
    print("\nExtracted Education Levels Sample:")
    print(df["education_levels_str"].value_counts().head(6))
    print("=" * 60 + "\n")

    return df

if __name__ == "__main__":
    clean_data()
