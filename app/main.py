#!/usr/bin/env python3
"""
SchemeSathi (स्कीम साथी)
AI-Powered Indian Government Scholarship & Welfare Scheme Finder
Modern, Minimal & High-Reliability UI
"""

import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Path setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
load_dotenv(PROJECT_ROOT / ".env", override=True)

from app.components.sidebar import render_sidebar
from app.components.disclaimer import render_disclaimer
from app.components.scheme_card import render_scheme_cards
from app.components.chat import render_quick_queries
from rag.retrieval import retrieve_schemes
from rag.generation import generate_answer
from ingestion.sqlite_index import get_scheme_by_slug

# Streamlit Page Configuration
st.set_page_config(
    page_title="SchemeSathi – AI Government Scholarship & Scheme Finder",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Minimalist Design System
st.markdown("""
<style>
    /* Global Base */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
    }
    
    /* Typography */
    h1, h2, h3, h4 {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
        color: #0F172A;
    }
    
    /* Hero Header */
    .hero-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        color: #0F172A;
        margin: 0;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #64748B;
        line-height: 1.5;
        margin-bottom: 1rem;
        max-width: 850px;
    }
    .hero-badge {
        background: #EFF6FF;
        color: #2563EB;
        border: 1px solid #BFDBFE;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Active Profile Strip */
    .active-profile-bar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        font-size: 0.82rem;
    }
    .profile-pill {
        background: #FFFFFF;
        color: #334155;
        border: 1px solid #CBD5E1;
        padding: 2px 10px;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.8rem;
    }
    .profile-label {
        font-weight: 600;
        color: #64748B;
        margin-right: 4px;
    }

    /* Buttons & Interactive Elements */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.15s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #2563EB;
        color: #2563EB;
    }
    
    /* Metric Card */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 2px;
    }
    
    /* Subtle scrollbar and dividers */
    hr {
        margin: 1.2rem 0;
        border-color: #F1F5F9;
    }
</style>
""", unsafe_allow_html=True)

def render_active_filters(profile: dict):
    """Renders a sleek horizontal pill bar showing active profile settings."""
    state = profile.get("state", "All India")
    edu = profile.get("education", "Any Education Level")
    cat = profile.get("category", "General")
    income = profile.get("income")
    gender = profile.get("gender", "all").capitalize()
    
    income_str = f"≤ ₹{income/100000:.1f}L" if income else "Any Income"
    
    st.markdown(
        f"""
        <div class="active-profile-bar">
            <span class="profile-label">🎯 Active Filters:</span>
            <span class="profile-pill">📍 {state}</span>
            <span class="profile-pill">🎓 {edu}</span>
            <span class="profile-pill">🏷️ {cat}</span>
            <span class="profile-pill">💰 {income_str}</span>
            <span class="profile-pill">⚧ {gender}</span>
            <span style="color:#94A3B8; font-size: 0.78rem; margin-left: auto;">(Adjust anytime in sidebar)</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def main():
    # Hero Title & Identity
    st.markdown(
        """
        <div class="hero-header">
            <span style="font-size: 2.2rem;">🎓</span>
            <div class="hero-title">SchemeSathi <span style="font-weight: 400; color: #64748B; font-size: 1.5rem;">(स्कीम साथी)</span></div>
            <span class="hero-badge">AI Gov Grants</span>
        </div>
        <div class="hero-subtitle">
            Instant discovery, eligibility verification & application guidance for 4,690+ Central and State Government scholarships, higher education grants, and citizen welfare schemes.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Minimal Provenance Notice
    render_disclaimer()

    # User Profile Controls in Sidebar
    profile = render_sidebar()

    # Active Filters Summary Strip
    render_active_filters(profile)

    # Initialize Chat History
    if "messages" not in st.session_state or not st.session_state.messages:
        state_label = profile.get("state", "All India")
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "**Namaste! 🙏 Welcome to SchemeSathi.**\n\n"
                    f"I am connected to a verified knowledge base of **4,693 Indian government schemes**.\n\n"
                    f"Your active filters are configured for **{state_label}** "
                    f"({profile.get('education', 'Any Education')}, Category: **{profile.get('category', 'General')}**).\n\n"
                    "Ask me about any scholarship or subsidy (e.g. *'Scholarships for girl students in engineering'*, "
                    "*'Fee reimbursement for SC/ST students'*, or *'Post-Matric grants under 2.5 Lakh'*), "
                    "or click a quick prompt below to begin!"
                ),
                "schemes": []
            }
        ]

    # Tabs: AI Chat vs Scheme Directory
    tab_chat, tab_browse = st.tabs(["💬 AI Assistant & Scheme Finder", "📚 Directory & Statistics"])

    with tab_chat:
        # Quick Explorations Pill Buttons
        quick_query = render_quick_queries()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Render Conversation Stream
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("schemes"):
                    render_scheme_cards(msg["schemes"])

        # Chat Input Box
        user_query = st.chat_input("Ask a question in English or Hinglish (e.g. 'Scholarships for 12th pass SC students in Maharashtra')...")

        # Handle quick button click if chosen
        if quick_query and not user_query:
            user_query = quick_query

        if user_query:
            # 1. Add user message
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # 2. Assistant Response Container
            with st.chat_message("assistant"):
                with st.spinner("🔍 Searching 4,693 government schemes and verifying eligibility rules..."):
                    # Retrieve matching candidate schemes
                    retrieved_schemes = retrieve_schemes(
                        query=user_query,
                        profile=profile,
                        top_k=profile.get("top_k", 8),
                        use_hybrid=profile.get("use_hybrid", True)
                    )

                    # Synthesize AI answer
                    answer = generate_answer(
                        query=user_query,
                        profile=profile,
                        retrieved_schemes=retrieved_schemes,
                        api_key=profile.get("api_key")
                    )

                    st.markdown(answer)
                    if retrieved_schemes:
                        render_scheme_cards(retrieved_schemes)

            # 3. Store assistant message in history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "schemes": retrieved_schemes
            })

    with tab_browse:
        st.markdown("### 📊 Knowledge Base Directory & Analytics")
        import pandas as pd
        from ingestion.clean_data import CLEAN_FILE_PATH

        if CLEAN_FILE_PATH.exists():
            df = pd.read_csv(CLEAN_FILE_PATH)

            # Minimalist KPI Metric Row
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-value">{len(df):,}</div>
                        <div class="metric-label">Total Schemes</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with kpi2:
                central_count = (df['scheme_scope'] == 'Central').sum()
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-value">{central_count:,}</div>
                        <div class="metric-label">Central Schemes</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with kpi3:
                state_count = (df['scheme_scope'] == 'State').sum()
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-value">{state_count:,}</div>
                        <div class="metric-label">State Schemes</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with kpi4:
                edu_count = (df['category'].str.contains('Education', na=False)).sum()
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-value">{edu_count:,}</div>
                        <div class="metric-label">Education Grants</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 🔍 Filter Directory by State")

            all_states = sorted(df["state_normalized"].unique().tolist())
            col_sel, col_srch = st.columns([1, 2])
            with col_sel:
                sel_state = st.selectbox("State / UT", options=["All"] + all_states, index=0)
            with col_srch:
                search_term = st.text_input("Search scheme by keyword", placeholder="Type name, category, or keyword...")

            filtered_df = df
            if sel_state != "All":
                filtered_df = filtered_df[filtered_df["state_normalized"] == sel_state]
            if search_term.strip():
                st_lower = search_term.lower()
                filtered_df = filtered_df[
                    filtered_df["name"].str.lower().str.contains(st_lower, na=False) |
                    filtered_df["category"].str.lower().str.contains(st_lower, na=False)
                ]

            disp_df = filtered_df[["name", "state_normalized", "scheme_scope", "category", "confidence_score", "official_url"]].head(100)

            st.dataframe(
                disp_df,
                column_config={
                    "official_url": st.column_config.LinkColumn("Official Portal", display_text="Visit Portal ↗"),
                    "name": "Scheme Name",
                    "state_normalized": "State",
                    "scheme_scope": "Scope",
                    "category": "Category",
                    "confidence_score": "Confidence"
                },
                use_container_width=True,
                hide_index=True
            )
            st.caption(f"Showing up to 100 matching schemes (out of {len(filtered_df):,} total).")
        else:
            st.warning("Cleaned dataset not found. Please run the ingestion pipeline.")

if __name__ == "__main__":
    main()
