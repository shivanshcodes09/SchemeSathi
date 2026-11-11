"""
SchemeSathi - Scheme Card Component
Renders structured, responsive, and minimal UI cards for government schemes.
"""

from typing import Dict, Any, List
import streamlit as st

def _safe_str(val: Any) -> str:
    """Safely converts any value (None, list, float) to cleaned string."""
    if val is None:
        return ""
    if isinstance(val, list):
        return ", ".join(str(x) for x in val if x)
    return str(val).strip()

def render_scheme_card(scheme: Dict[str, Any], index: int):
    """Renders an individual modern, minimal scheme card."""
    name = _safe_str(scheme.get("name")) or "Government Scheme"
    scope = _safe_str(scheme.get("scope")) or "Central"
    state = _safe_str(scheme.get("state")) or "Central"
    category = _safe_str(scheme.get("category"))
    ministry = _safe_str(scheme.get("ministry"))
    department = _safe_str(scheme.get("department"))
    confidence = _safe_str(scheme.get("confidence_score")) or "Medium"
    benefits = _safe_str(scheme.get("benefits"))
    eligibility = _safe_str(scheme.get("eligibility_summary")) or _safe_str(scheme.get("eligibility_text"))
    documents = _safe_str(scheme.get("documents_required"))
    process = _safe_str(scheme.get("application_process"))
    apply_url = _safe_str(scheme.get("apply_url"))
    official_url = _safe_str(scheme.get("official_url"))
    match_reasons = scheme.get("match_reasons") or []
    slug = _safe_str(scheme.get("slug")) or f"item_{index}"

    # Confidence styling
    if confidence == "High":
        conf_bg = "#ECFDF5"
        conf_text = "#065F46"
        conf_border = "#A7F3D0"
        conf_icon = "●"
    elif confidence == "Medium":
        conf_bg = "#FFFBEB"
        conf_text = "#92400E"
        conf_border = "#FDE68A"
        conf_icon = "●"
    else:
        conf_bg = "#FEF2F2"
        conf_text = "#991B1B"
        conf_border = "#FECACA"
        conf_icon = "○"

    is_central = (scope.lower() == "central" or state.lower() in ["central", "all india"])

    with st.container(border=True):
        # Header Row: Title & Confidence Tag
        col_title, col_meta = st.columns([4, 1.2])
        with col_title:
            st.markdown(
                f"<div style='font-size: 1.15rem; font-weight: 700; color: #0F172A; line-height: 1.35; margin-bottom: 4px;'>"
                f"<span style='color: #64748B; font-weight: 600; margin-right: 6px;'>#{index:02d}</span>{name}"
                f"</div>",
                unsafe_allow_html=True
            )
            # Badges row
            scope_badge = (
                "<span style='background:#EFF6FF; color:#1E40AF; border:1px solid #BFDBFE; "
                "padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:600; margin-right:6px;'>"
                "🏛️ Central Scheme</span>"
            ) if is_central else (
                f"<span style='background:#F0FDF4; color:#166534; border:1px solid #BBF7D0; "
                f"padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:600; margin-right:6px;'>"
                f"📍 State: {state}</span>"
            )
            cat_badge = (
                f"<span style='background:#F8FAFC; color:#475569; border:1px solid #E2E8F0; "
                f"padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:500; margin-right:6px;'>"
                f"{category}</span>"
            ) if category else ""

            st.markdown(f"<div style='margin-bottom: 6px;'>{scope_badge}{cat_badge}</div>", unsafe_allow_html=True)

            if ministry:
                nodal_text = f"{ministry}" + (f" ({department})" if department and department != ministry else "")
                st.markdown(
                    f"<div style='font-size: 0.8rem; color: #64748B; margin-bottom: 8px;'>"
                    f"🏢 <span style='font-weight: 500;'>Nodal Body:</span> {nodal_text}</div>",
                    unsafe_allow_html=True
                )

        with col_meta:
            st.markdown(
                f"<div style='text-align: right;'>"
                f"<span style='background:{conf_bg}; color:{conf_text}; border:1px solid {conf_border}; "
                f"padding:3px 10px; border-radius:9999px; font-size:11px; font-weight:600; display:inline-block;'>"
                f"{conf_icon} {confidence} Match</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        # Match Reasons (Eligibility verification points)
        if match_reasons:
            reasons_html = " ".join([
                f"<span style='background:#F0FDF4; color:#15803D; border:1px solid #DCFCE7; padding:2px 8px; border-radius:6px; font-size:11px; font-weight:500; margin-right:4px; display:inline-block; margin-bottom:4px;'>✓ {r}</span>"
                for r in match_reasons
            ])
            st.markdown(
                f"<div style='margin-bottom: 12px; padding: 6px 10px; background: #F8FAFC; border-radius: 8px; border-left: 3px solid #10B981;'>"
                f"<span style='font-size: 11px; font-weight: 600; color: #334155; margin-right: 6px;'>🎯 Profile Fit:</span>"
                f"{reasons_html}"
                f"</div>",
                unsafe_allow_html=True
            )

        # Content Grid: Benefits & Eligibility
        col_ben, col_elig = st.columns(2)
        with col_ben:
            st.markdown(
                "<div style='font-size: 0.82rem; font-weight: 700; color: #0F172A; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px;'>"
                "🎁 Key Benefits"
                "</div>",
                unsafe_allow_html=True
            )
            ben_snippet = benefits[:280] + ("..." if len(benefits) > 280 else "") if benefits else "Financial support, fee waiver, or grants as per official norms."
            st.markdown(
                f"<div style='font-size: 0.88rem; color: #334155; line-height: 1.5; background: #FAFAFA; padding: 10px 12px; border-radius: 8px; border: 1px solid #F1F5F9; min-height: 72px;'>"
                f"{ben_snippet}"
                f"</div>",
                unsafe_allow_html=True
            )

        with col_elig:
            st.markdown(
                "<div style='font-size: 0.82rem; font-weight: 700; color: #0F172A; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px;'>"
                "📋 Eligibility Criteria"
                "</div>",
                unsafe_allow_html=True
            )
            elig_snippet = eligibility[:280] + ("..." if len(eligibility) > 280 else "") if eligibility else "Open under standard central/state eligibility norms."
            st.markdown(
                f"<div style='font-size: 0.88rem; color: #334155; line-height: 1.5; background: #FAFAFA; padding: 10px 12px; border-radius: 8px; border: 1px solid #F1F5F9; min-height: 72px;'>"
                f"{elig_snippet}"
                f"</div>",
                unsafe_allow_html=True
            )

        # Expandable Details Drawer
        with st.expander("📑 Documents Required & Step-by-Step Application Procedure", expanded=False):
            tab_docs, tab_proc = st.tabs(["📄 Required Documents", "🚶 How to Apply"])
            with tab_docs:
                if documents:
                    st.markdown(f"<div style='font-size: 0.88rem; color: #334155;'>{documents}</div>", unsafe_allow_html=True)
                else:
                    st.info("Standard identification checklist: Aadhaar Card, State Domicile Certificate, Income Certificate, Educational Marksheets, and Active Bank Account Passbook.")
            with tab_proc:
                if process:
                    st.markdown(f"<div style='font-size: 0.88rem; color: #334155;'>{process}</div>", unsafe_allow_html=True)
                else:
                    st.info("Applications are accepted online via the official nodal portal. Register with your Mobile/Aadhaar, fill in personal and educational details, upload documents, and submit.")

        # Clean Action Bar
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        col_btn1, col_btn2, col_spacer = st.columns([1.2, 1.2, 2.5])
        
        with col_btn1:
            if official_url and official_url.startswith("http"):
                st.link_button("🏛️ Official Portal", official_url, use_container_width=True)
            else:
                st.button("🏛️ Details Link N/A", disabled=True, use_container_width=True, key=f"no_official_url_{index}_{slug}")
                
        with col_btn2:
            if apply_url and apply_url.startswith("http"):
                st.link_button("📝 Apply Now ↗", apply_url, use_container_width=True, type="primary")
            elif official_url and official_url.startswith("http"):
                # If apply_url is missing but official portal is available, direct to official portal
                st.link_button("📝 Apply on Portal ↗", official_url, use_container_width=True, type="primary")
            else:
                st.button("📝 Apply Link N/A", disabled=True, use_container_width=True, key=f"no_apply_url_{index}_{slug}")

def render_scheme_cards(schemes: List[Dict[str, Any]]):
    """Renders a collection of discovered scheme cards."""
    if not schemes:
        return
    st.markdown(
        f"<div style='margin-top: 1.2rem; margin-bottom: 0.8rem; display: flex; align-items: center; justify-content: space-between;'>"
        f"<span style='font-size: 1.15rem; font-weight: 700; color: #0F172A;'>🎯 Matching Schemes ({len(schemes)})</span>"
        f"<span style='font-size: 0.8rem; color: #64748B;'>Ranked by relevance & eligibility fit</span>"
        f"</div>",
        unsafe_allow_html=True
    )
    for idx, s in enumerate(schemes, 1):
        render_scheme_card(s, idx)
