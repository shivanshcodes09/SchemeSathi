#!/usr/bin/env python3
"""
SchemeSathi - Text Chunking Pipeline
Combines structured and descriptive scheme fields into a rich semantic chunk
designed for dense vector retrieval, preserving all critical context without
fragmenting scheme details.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
CLEAN_FILE_PATH = PROJECT_ROOT / "data" / "processed" / "schemes_clean.csv"

def safe_str(val: Any) -> str:
    """Null-safe string conversion."""
    if val is None or pd.isna(val):
        return ""
    return str(val).strip()

def build_scheme_chunk(row: pd.Series) -> str:
    """
    Constructs a structured descriptive text chunk for a single scheme record.
    """
    name = safe_str(row.get("name"))
    scope = safe_str(row.get("scheme_scope")) or "Central"
    state = safe_str(row.get("state_normalized")) or "All India"
    ministry = safe_str(row.get("ministry"))
    department = safe_str(row.get("department"))
    category = safe_str(row.get("category"))
    description = safe_str(row.get("description"))
    eligibility_text = safe_str(row.get("eligibility_text"))
    education = safe_str(row.get("education_levels_str")) or "Any Education Level"
    
    # Income limit text
    income_max = row.get("income_max_clean")
    if pd.notna(income_max) and income_max is not None:
        try:
            income_desc = f"Maximum annual family income up to ₹{int(float(income_max)):,}"
        except (ValueError, TypeError):
            income_desc = "Income limit not explicitly specified in official guidelines"
    else:
        income_desc = "Income limit not explicitly specified in official guidelines"
        
    caste = safe_str(row.get("caste_str")) or "All"
    gender = safe_str(row.get("gender_clean")) or "all"
    residence = safe_str(row.get("residence_clean")) or "both"
    
    # Special conditions
    special_conds = []
    if bool(row.get("bpl_required", False)):
        special_conds.append("BPL / Ration card mandatory")
    if bool(row.get("disability_required", False)):
        special_conds.append("Person with Disability (PwD) certificate required")
    special_str = " | ".join(special_conds) if special_conds else "Standard eligibility"
    
    benefits = safe_str(row.get("benefits"))
    documents = safe_str(row.get("documents_required"))
    process = safe_str(row.get("application_process"))

    chunk_lines = [
        f"Scheme: {name}",
        f"Scope: {scope} Government Scheme | State/UT Jurisdiction: {state}",
    ]
    if ministry:
        chunk_lines.append(f"Ministry / Department: {ministry} {('(' + department + ')') if department else ''}")
    if category:
        chunk_lines.append(f"Category: {category}")
        
    chunk_lines.append("")
    chunk_lines.append("Description & Objectives:")
    chunk_lines.append(description if description else "No formal description provided.")
    
    chunk_lines.append("")
    chunk_lines.append("Eligibility Criteria:")
    chunk_lines.append(eligibility_text if eligibility_text else "General public eligibility rules apply.")
    chunk_lines.append(f"Applicable Education: {education}")
    chunk_lines.append(f"Financial Criteria: {income_desc}")
    chunk_lines.append(f"Target Beneficiaries: {caste} | Gender: {gender.capitalize()} | Area: {residence.capitalize()}")
    if special_conds:
        chunk_lines.append(f"Special Status: {special_str}")
        
    chunk_lines.append("")
    chunk_lines.append("Benefits Provided:")
    chunk_lines.append(benefits if benefits else "Financial assistance, subsidy or direct benefit transfer as per scheme rules.")
    
    if documents:
        chunk_lines.append("")
        chunk_lines.append("Required Documents:")
        chunk_lines.append(documents)
        
    if process:
        chunk_lines.append("")
        chunk_lines.append("How to Apply:")
        chunk_lines.append(process)

    return "\n".join(chunk_lines).strip()

import ast

def parse_list_field(val: Any, default: List[str]) -> List[str]:
    """Safely parse a list or stringified list into clean list of strings."""
    if val is None or pd.isna(val):
        return list(default)
    if isinstance(val, (list, tuple)):
        clean = [str(x).strip(" '\"[]") for x in val if str(x).strip(" '\"[]")]
        return clean if clean else list(default)
    s = str(val).strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, (list, tuple)):
                clean = [str(x).strip(" '\"[]") for x in parsed if str(x).strip(" '\"[]")]
                return clean if clean else list(default)
        except Exception:
            pass
    clean = [p.strip(" '\"[]") for p in s.split(",") if p.strip(" '\"[]")]
    return clean if clean else list(default)

def generate_chunks(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Transforms DataFrame of schemes into chunks with complete metadata payloads.
    """
    chunks = []
    for _, row in df.iterrows():
        text = build_scheme_chunk(row)
        
        # Parse caste back to clean list
        caste_list = parse_list_field(row.get("caste_list"), ["All", "General"])

        # Parse education levels back to clean list
        edu_list = parse_list_field(row.get("education_levels"), ["Any Education Level"])

        income_val = row.get("income_max_clean")
        income_max = None
        if pd.notna(income_val) and income_val is not None:
            try:
                income_max = int(float(income_val))
            except (ValueError, TypeError):
                income_max = None

        payload = {
            "slug": safe_str(row.get("slug")),
            "name": safe_str(row.get("name")),
            "state": safe_str(row.get("state_normalized")) or "Central",
            "scope": safe_str(row.get("scheme_scope")) or "Central",
            "category": safe_str(row.get("category")),
            "ministry": safe_str(row.get("ministry")),
            "department": safe_str(row.get("department")),
            "education_levels": edu_list,
            "income_max": income_max,
            "caste": caste_list,
            "gender": safe_str(row.get("gender_clean")) or "all",
            "residence": safe_str(row.get("residence_clean")) or "both",
            "bpl_required": bool(row.get("bpl_required", False)),
            "disability_required": bool(row.get("disability_required", False)),
            "benefits": safe_str(row.get("benefits")),
            "eligibility_summary": safe_str(row.get("eligibility_text"))[:400],
            "documents_required": safe_str(row.get("documents_required")),
            "application_process": safe_str(row.get("application_process")),
            "apply_url": safe_str(row.get("apply_url")),
            "official_url": safe_str(row.get("official_url")),
            "confidence_score": safe_str(row.get("confidence_score")) or "Medium",
            "scraped_at": safe_str(row.get("scraped_at"))
        }
        
        chunks.append({
            "id": payload["slug"],
            "text": text,
            "payload": payload
        })
        
    logger.info(f"Generated {len(chunks)} scheme chunks.")
    return chunks

if __name__ == "__main__":
    df = pd.read_csv(CLEAN_FILE_PATH)
    chunks = generate_chunks(df)
    print(f"Sample Chunk (Total length: {len(chunks[0]['text'])} chars):\n")
    print(chunks[0]["text"][:600] + "\n...")
