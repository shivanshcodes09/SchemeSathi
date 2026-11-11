#!/usr/bin/env python3
"""
SchemeSathi - SQLite Structured Database Indexer & Query Engine
Stores cleaned structured scheme records for fast, exact demographic pre-filtering
before semantic vector search.
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
CLEAN_FILE_PATH = PROJECT_ROOT / "data" / "processed" / "schemes_clean.csv"
DB_PATH = PROJECT_ROOT / "data" / "processed" / "schemes.db"

def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Creates database schema and indexes if not already present."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schemes (
        slug TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        state TEXT NOT NULL,
        scope TEXT NOT NULL,
        category TEXT,
        ministry TEXT,
        department TEXT,
        education_levels TEXT,
        income_max INTEGER,
        caste TEXT,
        gender TEXT,
        residence TEXT,
        bpl_required INTEGER,
        disability_required INTEGER,
        benefits TEXT,
        eligibility_summary TEXT,
        documents_required TEXT,
        application_process TEXT,
        apply_url TEXT,
        official_url TEXT,
        confidence_score TEXT,
        scraped_at TEXT
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_state ON schemes(state);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scope ON schemes(scope);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_income ON schemes(income_max);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gender ON schemes(gender);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_residence ON schemes(residence);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bpl ON schemes(bpl_required);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_disability ON schemes(disability_required);")
    
    conn.commit()
    return conn

from ingestion.chunking import parse_list_field

def populate_db(df: pd.DataFrame, db_path: Path = DB_PATH):
    """Inserts or replaces all cleaned schemes into SQLite."""
    conn = init_db(db_path)
    cursor = conn.cursor()
    
    logger.info(f"Populating SQLite database at {db_path} with {len(df)} schemes...")
    
    records = []
    for _, row in df.iterrows():
        caste_parsed = parse_list_field(row.get("caste_list"), ["All", "General"])
        caste_json = json.dumps(caste_parsed)

        edu_parsed = parse_list_field(row.get("education_levels"), ["Any Education Level"])
        edu_str = ", ".join(edu_parsed)

        income_val = row.get("income_max_clean")
        income_max = int(float(income_val)) if pd.notna(income_val) and income_val is not None else None

        records.append((
            str(row.get("slug", "")),
            str(row.get("name", "")),
            str(row.get("state_normalized", "Central")),
            str(row.get("scheme_scope", "Central")),
            str(row.get("category", "")),
            str(row.get("ministry", "")),
            str(row.get("department", "")),
            edu_str,
            income_max,
            caste_json,
            str(row.get("gender_clean", "all")),
            str(row.get("residence_clean", "both")),
            1 if row.get("bpl_required", False) else 0,
            1 if row.get("disability_required", False) else 0,
            str(row.get("benefits", "")),
            str(row.get("eligibility_text", ""))[:400],
            str(row.get("documents_required", "")),
            str(row.get("application_process", "")),
            str(row.get("apply_url", "")),
            str(row.get("official_url", "")),
            str(row.get("confidence_score", "Medium")),
            str(row.get("scraped_at", ""))
        ))
        
    cursor.executemany("""
    INSERT OR REPLACE INTO schemes (
        slug, name, state, scope, category, ministry, department,
        education_levels, income_max, caste, gender, residence,
        bpl_required, disability_required, benefits, eligibility_summary,
        documents_required, application_process, apply_url, official_url,
        confidence_score, scraped_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
    conn.close()
    logger.success(f"Successfully indexed {count} schemes in SQLite DB.")

def query_eligible_slugs(profile: Dict[str, Any], db_path: Path = DB_PATH) -> Optional[List[str]]:
    """
    Executes multi-dimensional filter query based on user profile.
    Uses safe permissive fallbacks for unspecified or widely phrased fields.
    Returns None if DB does not exist, or List[str] of matching scheme slugs.
    """
    if not db_path.exists():
        if CLEAN_FILE_PATH.exists():
            logger.info(f"SQLite DB not found. Auto-populating from {CLEAN_FILE_PATH}...")
            df = pd.read_csv(CLEAN_FILE_PATH)
            populate_db(df, db_path=db_path)
        else:
            logger.warning(f"SQLite DB not found at {db_path}.")
            return None
        
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    clauses = ["1=1"]
    params = []
    
    # 1. State filter: include State's own schemes AND Central/All India schemes
    state = profile.get("state")
    if state and state not in ["All India", "All", "Central", "Any"]:
        clauses.append("(state = ? OR scope = 'Central' OR state = 'Central')")
        params.append(state)
        
    # 2. Income filter
    income = profile.get("income")
    if income is not None:
        try:
            inc_val = int(income)
            clauses.append("(income_max IS NULL OR income_max >= ?)")
            params.append(inc_val)
        except (ValueError, TypeError):
            pass

    # 3. Category / Caste filter
    category = profile.get("category")
    if category and category not in ["Any", "All"]:
        # Schemes open to All, General, or without caste restrictions ('[]'),
        # or schemes specific to the user's category (SC, ST, OBC, EWS, Minority)
        clauses.append("(caste = '[]' OR caste LIKE '%All%' OR caste LIKE '%General%' OR caste LIKE ?)")
        params.append(f"%{category}%")

    # 4. Gender filter
    gender = profile.get("gender")
    if gender and gender.lower() in ["male", "female"]:
        clauses.append("(gender = 'all' OR gender = ?)")
        params.append(gender.lower())

    # 5. Residence filter
    residence = profile.get("residence")
    if residence and residence.lower() in ["rural", "urban"]:
        clauses.append("(residence = 'both' OR residence = ?)")
        params.append(residence.lower())

    # 6. BPL card filter
    has_bpl = profile.get("bpl", False)
    if not has_bpl:
        clauses.append("bpl_required = 0")

    # 7. Disability filter
    has_disability = profile.get("disability", False)
    if not has_disability:
        clauses.append("disability_required = 0")

    # 8. Education level filter (permissive matching)
    edu = profile.get("education")
    if edu and edu not in ["Any", "All", "Any Education Level"]:
        edu_key = edu.split(" ")[0].strip()
        clauses.append("(education_levels LIKE ? OR education_levels LIKE '%Any Education Level%')")
        params.append(f"%{edu_key}%")

    query = f"SELECT slug FROM schemes WHERE {' AND '.join(clauses)}"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    slugs = [r[0] for r in rows]
    return slugs

def get_scheme_by_slug(slug: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetch complete structured record for a single scheme by slug."""
    if not db_path.exists():
        if CLEAN_FILE_PATH.exists():
            df = pd.read_csv(CLEAN_FILE_PATH)
            populate_db(df, db_path=db_path)
        else:
            return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schemes WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None

    rec = dict(row)
    # Parse JSON fields and align types with Qdrant payload schema
    if isinstance(rec.get("caste"), str):
        try:
            rec["caste"] = json.loads(rec["caste"])
        except Exception:
            rec["caste"] = [c.strip(" '\"[]") for c in rec["caste"].split(",") if c.strip(" '\"[]")]
    if not rec.get("caste"):
        rec["caste"] = ["All", "General"]

    if isinstance(rec.get("education_levels"), str):
        rec["education_levels"] = [e.strip(" '\"[]") for e in rec["education_levels"].split(",") if e.strip(" '\"[]")]

    rec["bpl_required"] = bool(rec.get("bpl_required", 0))
    rec["disability_required"] = bool(rec.get("disability_required", 0))
    return rec

if __name__ == "__main__":
    df = pd.read_csv(CLEAN_FILE_PATH)
    populate_db(df)
