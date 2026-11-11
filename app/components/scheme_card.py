"""
SchemeSathi - Scheme Card Component
Renders structured, responsive UI cards for discovered government schemes.
"""

from typing import Dict, Any, List
import streamlit as st

def render_scheme_card(scheme: Dict[str, Any], index: int):
    """Renders an individual scheme card with badges, benefits, and links."""
    name = scheme.get("name", "Government Scheme")
    scope = scheme.get("scope", "Central")
    state = scheme.get("state", "Central")
    category = scheme.get("category", "")
    ministry = scheme.get("ministry", "")
    department = scheme.get("department", "")
    confidence = scheme.get("confidence_score", "Medium")
    benefits = scheme.get("benefits", "")
    eligibility = scheme.get("eligibility_summary", scheme.get("eligibility_text", ""))
    documents = scheme.get("documents_required", "")
    process = scheme.get("application_process", "")
    apply_url = scheme.get("apply_url", "").strip()
    official_url = scheme.get("official_url", "").strip()
    match_reasons = scheme.get("match_reasons", [])

    conf_color = "#28a745" if confidence == "High" else "#ffc107" if confidence == "Medium" else "#dc3545"
    conf_badge = f"<span style='background-color:{conf_color}22; color:{conf_color}; border:1px solid {conf_color}; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:600;'>{confidence} Confidence</span>"
    
    scope_badge = "🏛️ **Central Scheme**" if scope == "Central" else f"📍 **State Scheme ({state})**"

    with st.container(border=True):
        col_title, col_conf = st.columns([4, 1])
        with col_title:
            st.markdown(f"#### {index}. {name}")
            st.markdown(f"{scope_badge} • *{category}*")
            if ministry:
                st.caption(f"**Nodal Authority:** {ministry} {('(' + department + ')') if department else ''}")
        with col_conf:
            st.markdown(conf_badge, unsafe_allow_html=True)

        # Match Reasons Callout
        if match_reasons:
            with st.expander("🎯 Why this matches your profile", expanded=False):
                for reason in match_reasons:
                    st.markdown(f"- ✅ {reason}")

        # Benefits & Eligibility
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 🎁 Benefits")
            if benefits:
                st.write(benefits[:300] + ("..." if len(benefits) > 300 else ""))
            else:
                st.write("*Financial or welfare grant as specified in official norms.*")
                
        with col2:
            st.markdown("##### 📋 Eligibility Overview")
            if eligibility:
                st.write(eligibility[:300] + ("..." if len(eligibility) > 300 else ""))
            else:
                st.write("*Open under standard eligibility guidelines.*")

        # Documents & Application Process in tabs
        with st.expander("📄 Required Documents & How to Apply"):
            t1, t2 = st.tabs(["Mandatory Documents", "Application Procedure"])
            with t1:
                if documents:
                    st.write(documents)
                else:
                    st.info("Standard identification (Aadhaar, domicile certificate, income certificate, bank passbook).")
            with t2:
                if process:
                    st.write(process)
                else:
                    st.info("Apply through the official central or state portal linked below.")

        # Action Buttons
        slug = scheme.get("slug", f"item_{index}")
        btn_cols = st.columns([1, 1, 2])
        with btn_cols[0]:
            if official_url and official_url.startswith("http"):
                st.link_button("🏛️ Official Portal", official_url, use_container_width=True)
            else:
                st.button("🏛️ No URL", disabled=True, use_container_width=True, key=f"no_official_url_{index}_{slug}")
        with btn_cols[1]:
            if apply_url and apply_url.startswith("http"):
                st.link_button("📝 Apply Now", apply_url, use_container_width=True, type="primary")
            else:
                st.button("📝 Apply Link N/A", disabled=True, use_container_width=True, key=f"no_apply_url_{index}_{slug}")

def render_scheme_cards(schemes: List[Dict[str, Any]]):
    """Renders a collection of scheme cards."""
    if not schemes:
        return
    st.markdown(f"### 🎯 Discovered Schemes ({len(schemes)} Matches)")
    for idx, s in enumerate(schemes, 1):
        render_scheme_card(s, idx)

