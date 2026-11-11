#!/usr/bin/env python3
"""
SchemeSathi - Grounded Answer Generation Engine (Gemini API)
Generates strictly grounded, empathetic, and actionable answers using retrieved
schemes context. Never invents deadlines, amounts, or eligibility guarantees.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag.citations import format_scheme_citations

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
DEFAULT_TEMP = float(os.getenv("LLM_TEMPERATURE", "0.1"))

SYSTEM_PROMPT = """You are SchemeSathi (स्कीम साथी), an expert AI assistant dedicated to helping Indian students, parents, and citizens discover verified government scholarships and welfare schemes.

CRITICAL RULES:
1. STRICT FACTUAL GROUNDING: Rely ONLY on the schemes provided in the Context below. Do not use outside knowledge or make assumptions.
2. NO HALLUCINATIONS: NEVER fabricate application deadlines, scholarship amounts, or eligibility conditions. If a detail (like exact income cap or deadline) is not in the context, explicitly say: "This detail is not specified in our official records. Please verify at the official portal."
3. NO ELIGIBILITY GUARANTEES: Never state that the user is guaranteed to receive a scheme. Use accurate terms like "You appear to meet the initial criteria for...", "You may qualify for...", or "Based on your details, this scheme matches...".
4. ACCESSIBILITY: Explain criteria clearly in simple, respectful language suitable for a high school student or parent.
5. EXPLICIT MATCH REASONS: For each recommended scheme, briefly explain WHY it matches their profile (e.g., domicile state, caste category, education level, or income ceiling).
6. APPLICATION STEPS & REQUIRED DOCUMENTS: Clearly summarize the mandatory documents and how to apply based on the retrieved text.
7. CITATIONS: Always reference the official scheme name exactly as provided in the context.
"""

def format_context_for_prompt(schemes: List[Dict[str, Any]]) -> str:
    """Formats retrieved scheme dictionaries into text context for the LLM."""
    if not schemes:
        return "No matching schemes found in records for this query and profile."
        
    blocks = []
    for idx, s in enumerate(schemes, 1):
        name = s.get("name", "Unknown Scheme")
        scope = s.get("scope", "Central")
        state = s.get("state", "All India")
        category = s.get("category", "")
        desc = s.get("description", "")
        eligibility = s.get("eligibility_summary", s.get("eligibility_text", ""))
        benefits = s.get("benefits", "")
        docs = s.get("documents_required", "")
        process = s.get("application_process", "")
        reasons = s.get("match_reasons", [])
        official_url = s.get("official_url", "")
        apply_url = s.get("apply_url", "")

        block = f"""--- SCHEME {idx}: {name} ---
Scope: {scope} | State: {state} | Category: {category}
Why it matches user profile: {'; '.join(reasons) if reasons else 'General demographic match'}
Overview: {desc}
Eligibility Details: {eligibility}
Benefits: {benefits}
Documents Needed: {docs if docs else 'Standard identification documents'}
How to Apply: {process if process else 'Apply via official portal'}
Official Link: {official_url}
Apply Link: {apply_url}
"""
        blocks.append(block.strip())
        
    return "\n\n".join(blocks)

def format_profile_for_prompt(profile: Dict[str, Any]) -> str:
    """Formats user demographic profile for the LLM prompt."""
    parts = []
    if profile.get("state"):
        parts.append(f"State/UT: {profile['state']}")
    if profile.get("education"):
        parts.append(f"Education: {profile['education']}")
    if profile.get("income") is not None:
        parts.append(f"Annual Income: ₹{profile['income']:,}")
    if profile.get("category"):
        parts.append(f"Category: {profile['category']}")
    if profile.get("gender"):
        parts.append(f"Gender: {profile['gender'].capitalize()}")
    if profile.get("residence"):
        parts.append(f"Area: {profile['residence'].capitalize()}")
    if profile.get("bpl"):
        parts.append("Has BPL/Ration Card: Yes")
    if profile.get("disability"):
        parts.append("Person with Disability (PwD): Yes")
        
    return " | ".join(parts) if parts else "General profile"

def generate_answer(
    query: str,
    profile: Dict[str, Any],
    retrieved_schemes: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL
) -> str:
    """
    Generates a grounded LLM answer using Google Gemini API,
    with an intelligent fallback if API key is not configured.
    """
    effective_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    
    # If no schemes retrieved
    if not retrieved_schemes:
        user_state = profile.get("state", "your state")
        return (
            f"### 🔍 No Matching Schemes Found\n\n"
            f"We couldn't find any verified government schemes matching your exact profile for **{user_state}** in our current dataset.\n\n"
            f"**Suggestions:**\n"
            f"- Try broadening your education or category filters in the sidebar.\n"
            f"- Select **'All India'** to view Central Government scholarships open nationwide.\n"
            f"- Visit the official National Scholarship Portal at [scholarships.gov.in](https://scholarships.gov.in) or [myscheme.gov.in](https://myscheme.gov.in) to explore recently updated state notifications."
        )

    # If Gemini API Key is available, generate via LLM
    if effective_key and effective_key != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=effective_key)
            
            context_text = format_context_for_prompt(retrieved_schemes)
            profile_text = format_profile_for_prompt(profile)
            
            user_prompt = f"""USER PROFILE:
{profile_text}

USER QUESTION:
{query}

RETRIEVED SCHEMES CONTEXT:
{context_text}

Please provide a structured, helpful answer addressing the user's question. For each relevant scheme, explain what it offers, why the user may qualify, the key documents required, and the next steps to apply."""

            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config={"temperature": DEFAULT_TEMP, "max_output_tokens": 1500}
            )
            
            response = model.generate_content(user_prompt)
            llm_text = response.text
            
            # Attach source citations
            citations_block = format_scheme_citations(retrieved_schemes)
            return f"{llm_text}\n\n{citations_block}"
            
        except Exception as e:
            logger.warning(f"Gemini API call failed ({e}). Using deterministic structured response...")

    # Deterministic fallback mode (generates clean structured answer without external LLM)
    return generate_deterministic_answer(query, profile, retrieved_schemes)

def generate_deterministic_answer(
    query: str,
    profile: Dict[str, Any],
    schemes: List[Dict[str, Any]]
) -> str:
    """
    High-quality deterministic fallback summary for offline or API-key-free usage.
    """
    lines = [
        f"Based on your profile and query, here are **{len(schemes)} potentially relevant government schemes** discovered in verified records:",
        ""
    ]

    for idx, s in enumerate(schemes, 1):
        name = s.get("name", "Government Scheme")
        scope = s.get("scope", "Central")
        state = s.get("state", "Central")
        benefits = s.get("benefits", "Assistance as per guidelines.")
        eligibility = s.get("eligibility_summary", s.get("eligibility_text", ""))
        docs = s.get("documents_required", "")
        process = s.get("application_process", "")
        reasons = s.get("match_reasons", [])

        lines.append(f"### {idx}. {name}")
        lines.append(f"- **Scope & Jurisdiction:** {scope} Scheme ({state})")
        if reasons:
            lines.append(f"- **Why you may qualify:** {reasons[0]}")
        if benefits:
            lines.append(f"- **Key Benefits:** {benefits[:250]}...")
        if eligibility:
            lines.append(f"- **Eligibility Summary:** {eligibility[:200]}...")
        if docs:
            lines.append(f"- **Mandatory Documents:** {docs[:200]}...")
        if process:
            lines.append(f"- **How to Apply:** {process[:200]}...")
        lines.append("")

    citations_block = format_scheme_citations(schemes)
    lines.append(citations_block)
    return "\n".join(lines)

if __name__ == "__main__":
    sample_schemes = [{
        "name": "Post Matric Scholarship for SC Students",
        "scope": "Central",
        "state": "All India",
        "benefits": "Covers tuition fees and maintenance allowance.",
        "eligibility_summary": "SC students pursuing post-matric courses with family income <= 2.5L.",
        "documents_required": "Income certificate, Caste certificate, Marks sheet",
        "application_process": "Apply online at scholarships.gov.in",
        "official_url": "https://myscheme.gov.in/schemes/pms-sc",
        "apply_url": "https://scholarships.gov.in",
        "match_reasons": ["Applicable across India", "Income ceiling matches", "Category SC matches"],
        "confidence_score": "High",
        "scraped_at": "2025-01-15"
    }]
    profile = {"state": "Punjab", "income": 200000, "category": "SC"}
    print(generate_answer("How can I apply for post matric scholarship?", profile, sample_schemes))

