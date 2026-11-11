"""
SchemeSathi - Interactive Chat & Suggested Query Component
"""

import streamlit as st
from typing import Optional

SUGGESTED_TOPICS = [
    {
        "icon": "👩‍🎓",
        "title": "Girl Student Grants",
        "query": "What are the best scholarships and financial assistance schemes for girl students?"
    },
    {
        "icon": "🎓",
        "title": "College & Undergrad",
        "query": "Scholarships, fee waivers, and maintenance grants for college and undergraduate degree students."
    },
    {
        "icon": "💰",
        "title": "Income < ₹2.5 Lakh",
        "query": "Post-matric and pre-matric scholarships for students from families with annual income below 2.5 Lakh."
    },
    {
        "icon": "🔬",
        "title": "PhD & Research",
        "query": "Higher education fellowships and national research grants for PhD, MPhil, and postgraduate scholars."
    },
    {
        "icon": "🏛️",
        "title": "SC/ST/OBC Grants",
        "query": "Tuition fee reimbursement and welfare scholarship schemes for SC, ST, and OBC category students."
    }
]

def render_quick_queries() -> Optional[str]:
    """Renders sleek one-click pill buttons for popular inquiries."""
    st.markdown(
        "<div style='font-size: 0.85rem; font-weight: 600; color: #64748B; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;'>"
        "💡 Quick Explorations"
        "</div>",
        unsafe_allow_html=True
    )
    cols = st.columns(len(SUGGESTED_TOPICS))
    for idx, item in enumerate(SUGGESTED_TOPICS):
        with cols[idx]:
            button_label = f"{item['icon']} {item['title']}"
            if st.button(button_label, key=f"quick_pill_{idx}", use_container_width=True, help=item["query"]):
                return item["query"]
    return None
