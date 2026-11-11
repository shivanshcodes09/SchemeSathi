"""
SchemeSathi - Freshness & Provenance Disclaimer Component
"""

import streamlit as st

def render_disclaimer():
    """Renders data freshness banner and informational notice."""
    st.info(
        "💡 **Data Provenance & Freshness Notice:** Scheme knowledge base contains **4,693 government schemes** "
        "sourced from official [myScheme.gov.in](https://myscheme.gov.in) (Ministry of Electronics and Information Technology, GoI). "
        "Scheme rules, funding quotas, and application deadlines may be updated by nodal ministries; "
        "always verify current guidelines on the official portal before applying.",
        icon="ℹ️"
    )

