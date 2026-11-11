#!/usr/bin/env python3
"""
SchemeSathi (स्कीम साथी)
AI-Powered Indian Government Scholarship & Welfare Scheme Finder
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

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .stButton>button {
        border-radius: 8px;
    }
    .badge-box {
        background-color: #F3F4F6;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header Branding
    st.markdown("<div class='main-header'>🎓 SchemeSathi (स्कीम साथी)</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>AI-Powered Discovery Engine for Indian Government Scholarships, "
        "Higher Education Grants & Citizen Welfare Schemes.</div>",
        unsafe_allow_html=True
    )

    # Top Notice
    render_disclaimer()

    # User Profile Sidebar
    profile = render_sidebar()

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Namaste! 🙏 I am **SchemeSathi**, your AI guide to Indian government scholarships and welfare schemes.\n\n"
                    f"Your current profile filter is set to **{profile['state']}** ({profile['education']}, Category: {profile['category']}).\n\n"
                    "Ask me a question below (e.g. *'What scholarships are available for girl students?'* or *'Fee waiver schemes for engineering'*) "
                    "or click one of the popular topics to get started!"
                ),
                "schemes": []
            }
        ]

    # Tabs: AI Chat vs Browse Schemes Directory
    tab_chat, tab_browse = st.tabs(["💬 AI Assistant & Scheme Finder", "📚 Directory & Stats"])

    with tab_chat:
        # Quick Query buttons
        quick_clicked = render_quick_queries()

        st.markdown("---")

        # Display Chat History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("schemes"):
                    render_scheme_cards(msg["schemes"])

        # Chat Input
        user_query = st.chat_input("Ask a question in English or Hinglish (e.g. 'Scholarships for 12th pass SC students in Maharashtra')...")

        # Handle quick button click if clicked
        if quick_clicked and not user_query:
            user_query = quick_clicked

        if user_query:
            # 1. Add user message
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # 2. Assistant Response Container
            with st.chat_message("assistant"):
                with st.spinner("Searching 4,693 government schemes and verifying eligibility rules..."):
                    # Retrieve
                    retrieved_schemes = retrieve_schemes(
                        query=user_query,
                        profile=profile,
                        top_k=profile.get("top_k", 8),
                        use_hybrid=profile.get("use_hybrid", True)
                    )
                    
                    # Generate Answer
                    answer = generate_answer(
                        query=user_query,
                        profile=profile,
                        retrieved_schemes=retrieved_schemes,
                        api_key=profile.get("api_key")
                    )

                    st.markdown(answer)
                    if retrieved_schemes:
                        render_scheme_cards(retrieved_schemes)

            # Save in history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "schemes": retrieved_schemes
            })

    with tab_browse:
        st.markdown("### 📊 Scheme Knowledge Base Overview")
        import pandas as pd
        from ingestion.clean_data import CLEAN_FILE_PATH
        if CLEAN_FILE_PATH.exists():
            df = pd.read_csv(CLEAN_FILE_PATH)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Schemes", f"{len(df):,}")
            m2.metric("Central Schemes", f"{(df['scheme_scope'] == 'Central').sum():,}")
            m3.metric("State Schemes", f"{(df['scheme_scope'] == 'State').sum():,}")
            m4.metric("Education Schemes", f"{(df['category'].str.contains('Education', na=False)).sum():,}")

            st.markdown("#### 🔍 Filter Directory by State")
            sel_state = st.selectbox("Select State to View Schemes", options=["All"] + sorted(df["state_normalized"].unique().tolist()))
            
            if sel_state == "All":
                disp_df = df[["name", "state_normalized", "scheme_scope", "category", "confidence_score", "official_url"]].head(50)
            else:
                disp_df = df[df["state_normalized"] == sel_state][["name", "state_normalized", "scheme_scope", "category", "confidence_score", "official_url"]]

            st.dataframe(
                disp_df,
                column_config={
                    "official_url": st.column_config.LinkColumn("Official Portal"),
                    "name": "Scheme Name",
                    "state_normalized": "State",
                    "scheme_scope": "Scope",
                    "category": "Category",
                    "confidence_score": "Confidence"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Cleaned dataset not found. Please run the ingestion pipeline.")

if __name__ == "__main__":
    main()

