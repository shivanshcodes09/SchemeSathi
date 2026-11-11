"""
SchemeSathi - Sidebar Profile Component
Renders the 8-dimension user profile filter in Streamlit with modern, minimal styling.
"""

from typing import Dict, Any
import streamlit as st

STATES_LIST = [
    "All India",
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry"
]

EDUCATION_LEVELS = [
    "Any Education Level",
    "Below 10th",
    "10th Pass / Secondary",
    "12th Pass / Higher Secondary",
    "Diploma / Polytechnic",
    "Graduation / Undergraduate",
    "Post-Graduation",
    "PhD / Research"
]

INCOME_BRACKETS = [
    ("Unspecified / Any Income", None),
    ("Below ₹1,00,000 (1 Lakh)", 100000),
    ("₹1,00,000 to ₹2,50,000 (2.5 Lakh)", 250000),
    ("₹2,50,000 to ₹5,00,000 (5 Lakh)", 500000),
    ("₹5,00,000 to ₹8,00,000 (8 Lakh)", 800000),
    ("Above ₹8,00,000", 1500000)
]

CATEGORIES = [
    "All / General",
    "SC (Scheduled Caste)",
    "ST (Scheduled Tribe)",
    "OBC (Other Backward Class)",
    "EWS (Economically Weaker Section)",
    "Minority"
]

def render_sidebar() -> Dict[str, Any]:
    """Renders user profile controls in the sidebar and returns profile dict."""
    with st.sidebar:
        st.markdown(
            "<div style='margin-bottom: 0.8rem;'>"
            "<div style='font-size: 1.25rem; font-weight: 700; color: #0F172A;'>👤 Eligibility Profile</div>"
            "<div style='font-size: 0.82rem; color: #64748B;'>Set your profile to filter 4,690+ schemes instantly.</div>"
            "</div>",
            unsafe_allow_html=True
        )

        # 1. State / Domicile
        state = st.selectbox(
            "📍 State of Domicile",
            options=STATES_LIST,
            index=0,
            help="Select your state. 'All India' includes all Central Government schemes."
        )

        # 2. Education Level
        education = st.selectbox(
            "🎓 Education Level",
            options=EDUCATION_LEVELS,
            index=0,
            help="Select your ongoing or completed education stage."
        )

        # 3. Caste / Social Category
        cat_choice = st.selectbox(
            "🏷️ Social Category",
            options=CATEGORIES,
            index=0,
            help="Specific schemes are earmarked for reserved categories or EWS."
        )
        cat_clean = cat_choice.split(" ")[0].strip() if "(" in cat_choice else "General"
        if cat_clean == "All":
            cat_clean = "General"

        # 4. Family Annual Income
        income_choice = st.selectbox(
            "💰 Annual Family Income",
            options=[b[0] for b in INCOME_BRACKETS],
            index=0,
            help="Many scholarships require family income below ₹2.5L or ₹8.0L."
        )
        income_val = next((val for label, val in INCOME_BRACKETS if label == income_choice), None)

        # 5. Gender & Residence in neat compact columns
        col_g, col_r = st.columns(2)
        with col_g:
            gender = st.selectbox(
                "⚧ Gender",
                options=["All / Any", "Female", "Male"],
                index=0,
                help="Many high-value scholarships are dedicated to girl students."
            )
            gender_clean = "all" if "All" in gender else gender.lower()

        with col_r:
            residence = st.selectbox(
                "🏡 Area",
                options=["Both / Any", "Rural", "Urban"],
                index=0
            )
            residence_clean = "both" if "Both" in residence else residence.lower()

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size: 0.8rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;'>"
            "Special Status"
            "</div>",
            unsafe_allow_html=True
        )

        # 6. BPL & PwD checkboxes
        has_bpl = st.checkbox(
            "BPL / Antyodaya Ration Card",
            value=False,
            help="Unlocks schemes exclusively reserved for Below Poverty Line families."
        )

        has_disability = st.checkbox(
            "Person with Disability (PwD ≥ 40%)",
            value=False,
            help="Unlocks disability reservations and assistive device grants."
        )

        # Reset chat session button in sidebar
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Reset Chat Session", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        # Advanced Settings Accordion
        with st.expander("⚙️ Advanced RAG & LLM Settings", expanded=False):
            api_key = st.text_input(
                "Gemini API Key (optional)",
                type="password",
                help="Enter your Gemini key to use LLM generation, or configure GEMINI_API_KEY in .env"
            )
            use_hybrid = st.checkbox("Hybrid Search (BM25 + Dense Vectors)", value=True)
            top_k = st.slider("Max Schemes Retrieved", min_value=3, max_value=15, value=8)

        profile = {
            "state": state,
            "education": education,
            "income": income_val,
            "category": cat_clean,
            "gender": gender_clean,
            "residence": residence_clean,
            "bpl": has_bpl,
            "disability": has_disability,
            "api_key": api_key,
            "use_hybrid": use_hybrid,
            "top_k": top_k
        }

        return profile
