"""
SchemeSathi - Freshness & Provenance Disclaimer Component
"""

import streamlit as st

def render_disclaimer():
    """Renders a sleek, minimal provenance notice."""
    with st.expander("ℹ️ Official Data Source: 4,693 Verified Schemes (myScheme.gov.in)", expanded=False):
        st.markdown(
            """
            - **Source**: Directly indexed from official [myScheme.gov.in](https://myscheme.gov.in) 
              (National Portal by Ministry of Electronics & IT, Government of India).
            - **Notice**: Eligibility rules, financial allocations, and application deadlines are managed by nodal ministries. 
              Always verify active guidelines on the official portal links provided before applying.
            """
        )
