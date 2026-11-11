#!/usr/bin/env python3
"""
SchemeSathi - Deterministic Eligibility Matching Engine
Evaluates candidate government schemes against user demographic profiles.
Provides explicit, explainable matching reasons and hard rule enforcement
to prevent LLM hallucination in eligibility assessment.
"""

from typing import Dict, Any, List, Tuple

def evaluate_scheme_eligibility(
    scheme: Dict[str, Any],
    profile: Dict[str, Any]
) -> Tuple[bool, List[str], List[str]]:
    """
    Evaluates whether a user profile satisfies a scheme's criteria.
    Returns:
        is_eligible (bool): Whether the scheme passes all hard requirements.
        match_reasons (List[str]): Explanations of criteria satisfied.
        mismatch_reasons (List[str]): Explanations of criteria failed.
    """
    match_reasons = []
    mismatch_reasons = []

    # 1. State / Domicile Check
    user_state = profile.get("state")
    scheme_state = scheme.get("state", "Central")
    scheme_scope = scheme.get("scope", "Central")
    
    if scheme_scope == "Central" or scheme_state in ["Central", "All", "All India"]:
        match_reasons.append(f"Central government scheme applicable across India (including {user_state or 'your state'}).")
    elif user_state and user_state not in ["All India", "Any"]:
        if user_state.lower() == scheme_state.lower() or user_state.lower() in scheme_state.lower():
            match_reasons.append(f"State scheme matches your domicile state ({user_state}).")
        else:
            mismatch_reasons.append(f"Scheme is designated specifically for {scheme_state}, not {user_state}.")
    else:
        match_reasons.append(f"Scheme jurisdiction: {scheme_state}.")

    # 2. Income Limit Check
    user_income = profile.get("income")
    scheme_income_max = scheme.get("income_max")
    
    if scheme_income_max is not None and scheme_income_max > 0:
        if user_income is not None:
            if user_income <= scheme_income_max:
                match_reasons.append(f"Your annual family income (₹{user_income:,}) is within the ceiling of ₹{scheme_income_max:,}.")
            else:
                mismatch_reasons.append(f"Your family income (₹{user_income:,}) exceeds the maximum eligibility limit of ₹{scheme_income_max:,}.")
        else:
            match_reasons.append(f"Scheme income ceiling is ₹{scheme_income_max:,} (your income was not specified).")
    else:
        match_reasons.append("Income limit is not explicitly capped in official records.")

    # 3. Category / Caste Check
    user_category = profile.get("category")
    scheme_caste = scheme.get("caste", [])
    if isinstance(scheme_caste, str):
        try:
            import json, ast
            if scheme_caste.startswith("["):
                try:
                    scheme_caste = json.loads(scheme_caste)
                except Exception:
                    scheme_caste = ast.literal_eval(scheme_caste)
            else:
                scheme_caste = [c.strip(" '\"[]") for c in scheme_caste.split(",") if c.strip(" '\"[]")]
        except Exception:
            scheme_caste = [c.strip(" '\"[]") for c in scheme_caste.split(",") if c.strip(" '\"[]")]

    if isinstance(scheme_caste, (list, tuple)):
        scheme_caste = [str(c).strip(" '\"[]") for c in scheme_caste if str(c).strip(" '\"[]")]
    else:
        scheme_caste = []

    caste_lower = [c.lower() for c in scheme_caste]
    is_open_to_all = len(caste_lower) == 0 or "all" in caste_lower or "general" in caste_lower

    if user_category and user_category not in ["Any", "All"]:
        u_cat_lower = user_category.lower()
        if is_open_to_all:
            match_reasons.append(f"Open to all categories (including {user_category}).")
        elif any(u_cat_lower in c or c in u_cat_lower for c in caste_lower):
            match_reasons.append(f"Open to your category ({user_category}).")
        else:
            mismatch_reasons.append(f"Restricted to categories: {', '.join(scheme_caste)}, not {user_category}.")
    else:
        match_reasons.append(f"Category eligibility: {', '.join(scheme_caste) if scheme_caste else 'All categories'}.")

    # 4. Gender Check
    user_gender = profile.get("gender")
    scheme_gender = str(scheme.get("gender", "all")).lower()
    
    if user_gender and user_gender.lower() in ["male", "female"]:
        u_gen_lower = user_gender.lower()
        if scheme_gender in ["all", "both"] or scheme_gender == u_gen_lower:
            match_reasons.append(f"Gender eligibility criteria satisfied ({scheme_gender.capitalize()}).")
        else:
            mismatch_reasons.append(f"Designated exclusively for {scheme_gender.capitalize()} applicants.")

    # 5. Residence Check (Rural / Urban)
    user_residence = profile.get("residence")
    scheme_residence = str(scheme.get("residence", "both")).lower()
    
    if user_residence and user_residence.lower() in ["rural", "urban"]:
        u_res_lower = user_residence.lower()
        if scheme_residence in ["both", "all"] or scheme_residence == u_res_lower:
            match_reasons.append(f"Residence area requirement met ({scheme_residence.capitalize()}).")
        else:
            mismatch_reasons.append(f"Restricted to {scheme_residence.capitalize()} residents only.")

    # 6. BPL Status Check
    user_has_bpl = profile.get("bpl", False)
    scheme_bpl_req = bool(scheme.get("bpl_required", False))
    
    if scheme_bpl_req:
        if user_has_bpl:
            match_reasons.append("BPL / Ration card requirement satisfied.")
        else:
            mismatch_reasons.append("Requires Below Poverty Line (BPL) / Antyodaya Ration card.")

    # 7. Disability Status Check
    user_has_disability = profile.get("disability", False)
    scheme_disability_req = bool(scheme.get("disability_required", False))
    
    if scheme_disability_req:
        if user_has_disability:
            match_reasons.append("Person with Disability (PwD) requirement satisfied.")
        else:
            mismatch_reasons.append("Exclusively reserved for Persons with Disabilities (PwD).")

    # 8. Education Level Check
    user_edu = profile.get("education")
    scheme_edu = scheme.get("education_levels", [])
    if isinstance(scheme_edu, str):
        try:
            import json, ast
            if scheme_edu.startswith("["):
                try:
                    scheme_edu = json.loads(scheme_edu)
                except Exception:
                    scheme_edu = ast.literal_eval(scheme_edu)
            else:
                scheme_edu = [e.strip(" '\"[]") for e in scheme_edu.split(",") if e.strip(" '\"[]")]
        except Exception:
            scheme_edu = [e.strip(" '\"[]") for e in scheme_edu.split(",") if e.strip(" '\"[]")]

    if isinstance(scheme_edu, (list, tuple)):
        scheme_edu = [str(e).strip(" '\"[]") for e in scheme_edu if str(e).strip(" '\"[]")]
    else:
        scheme_edu = []

    if user_edu and user_edu not in ["Any", "All", "Any Education Level"]:
        u_edu_lower = user_edu.lower()
        edu_lower = [e.lower() for e in scheme_edu]
        if not edu_lower or "any education level" in edu_lower or any(u_edu_lower in e or e in u_edu_lower for e in edu_lower):
            match_reasons.append(f"Applicable to education level: {user_edu}.")
        else:
            # Soft mismatch note: education in schemes often has wide phrasing
            match_reasons.append(f"Scheme mentions levels: {', '.join(scheme_edu)}.")

    is_eligible = len(mismatch_reasons) == 0
    return is_eligible, match_reasons, mismatch_reasons

def filter_schemes_by_eligibility(
    schemes: List[Dict[str, Any]],
    profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Filters a list of candidate schemes, attaching match explanations
    and discarding hard mismatches.
    """
    eligible_schemes = []
    for s in schemes:
        is_ok, matches, mismatches = evaluate_scheme_eligibility(s, profile)
        if is_ok:
            s_copy = s.copy()
            s_copy["match_reasons"] = matches
            s_copy["mismatch_reasons"] = mismatches
            eligible_schemes.append(s_copy)
    return eligible_schemes

if __name__ == "__main__":
    test_scheme = {
        "name": "Post-Matric Scholarship for SC",
        "state": "Maharashtra",
        "scope": "State",
        "income_max": 250000,
        "caste": ["SC"],
        "gender": "all",
        "residence": "both",
        "bpl_required": False,
        "disability_required": False,
        "education_levels": ["Graduation / Undergraduate", "Post-Graduation"]
    }
    
    test_profile = {
        "state": "Maharashtra",
        "income": 180000,
        "category": "SC",
        "gender": "female",
        "residence": "urban",
        "bpl": False,
        "disability": False,
        "education": "Graduation / Undergraduate"
    }
    
    ok, match_res, mismatch_res = evaluate_scheme_eligibility(test_scheme, test_profile)
    print(f"Eligible: {ok}")
    print("Match reasons:", match_res)
    print("Mismatch reasons:", mismatch_res)

