"""
SchemeSathi - Interactive Chat & Natural Language Query Component
"""

import streamlit as st
from typing import Dict, Any, List

SUGGESTED_QUERIES = [
    "🎓 Scholarships for college and undergraduate degree students",
    "👧 Best financial assistance schemes for girl students",
    "💼 Post-Matric scholarships for family income below 2.5 Lakh",
    "🔬 Higher education and PhD research fellowship schemes",
    "🚜 Welfare and fee reimbursement schemes for SC/ST/OBC students"
]

def render_quick_queries():
    """Renders one-click pill buttons for popular scholarship inquiries."""
    st.markdown("##### 💡 Popular Questions")
    cols = st.columns(len(SUGGESTED_QUERIES))
    for idx, prompt in enumerate(SUGGESTED_QUERIES):
        with cols[idx]:
            # Clean label for button
            label = prompt.split(" ")[0] + " " + " ".join(prompt.split(" ")[1:3])
            if st.button(label, key=f"quick_btn_{idx}", use_container_width=True, help=prompt):
                return prompt
    return None

