#!/usr/bin/env python3
"""
SchemeSathi - Source Citations & Provenance Engine
Extracts, formats, and attaches verified official portal and application links
to scheme recommendations, providing complete provenance and transparency.
"""

from typing import List, Dict, Any

def format_scheme_citations(schemes: List[Dict[str, Any]]) -> str:
    """
    Constructs a clean Markdown citation block from retrieved scheme objects.
    """
    if not schemes:
        return ""

    citation_lines = [
        "",
        "---",
        "### 🔗 Official Sources & Application Links",
        ""
    ]

    for idx, s in enumerate(schemes, 1):
        name = s.get("name", "Government Scheme")
        state = s.get("state", "Central")
        scope = s.get("scope", "Central")
        official_url = s.get("official_url", "").strip()
        apply_url = s.get("apply_url", "").strip()
        confidence = s.get("confidence_score", "Medium")
        scraped_at = s.get("scraped_at", "")

        conf_emoji = "🟢" if confidence == "High" else "🟡" if confidence == "Medium" else "🔴"
        badge = "🏛️ Central" if scope == "Central" else f"📍 State ({state})"

        header = f"**{idx}. {name}** — {badge} {conf_emoji}"
        citation_lines.append(header)

        links = []
        if official_url and official_url.startswith("http"):
            links.append(f"[🏛️ Official Portal / Guidelines]({official_url})")
        if apply_url and apply_url.startswith("http"):
            links.append(f"[📝 Apply Online]({apply_url})")
            
        if links:
            citation_lines.append("   " + " | ".join(links))
        else:
            citation_lines.append("   *Official portal link not available in records. Please check the National Scholarship Portal (scholarships.gov.in) or state department portal.*")

        if scraped_at:
            citation_lines.append(f"   *Record captured: {scraped_at[:10]}*")

        citation_lines.append("")

    citation_lines.append(
        "> ⚠️ **Disclaimer:** *SchemeSathi is an AI informational tool and does not guarantee eligibility or process applications. Criteria, deadlines, and funding quotas change dynamically. Always confirm details on the official government portal before applying.*"
    )

    return "\n".join(citation_lines)

if __name__ == "__main__":
    sample = [{
        "name": "PM-YASASVI Scheme",
        "state": "Central",
        "scope": "Central",
        "official_url": "https://myscheme.gov.in/schemes/pm-yasasvi",
        "apply_url": "https://yet.nta.ac.in",
        "confidence_score": "High",
        "scraped_at": "2025-01-15T00:00:00"
    }]
    print(format_scheme_citations(sample))

