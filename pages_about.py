"""AcadFlow — About Page"""
import streamlit as st
import ui


def show(user: dict):
    home = {"admin": "Admin Home", "officer": "Officer Home"}.get(user.get("role"), "Student Home")
    ui.render_chrome(user, "About AcadFlow", ui.BRAND_TAGLINE, breadcrumbs=[home, "About AcadFlow"])

    st.markdown(
        f'<div class="af-hero">'
        f'<div><h1>{ui.BRAND_NAME}</h1><p>{ui.BRAND_DESC}</p></div>'
        f'<div class="af-hero-pill">Google Gemini + Hybrid RAG</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            '<div class="card"><h3>🧠 Multi-Agent Architecture</h3>'
            '<ul style="color:#475569;font-size:.88rem;line-height:1.7">'
            '<li><strong>Orchestrator Agent:</strong> Routes greetings vs institutional RAG queries.</li>'
            '<li><strong>Hybrid Retrieval Agent:</strong> BM25 + ChromaDB + RRF + lexical reranking.</li>'
            '<li><strong>Knowledge & Synthesis Agent:</strong> Grounded answers with page citations.</li>'
            '<li><strong>Eligibility & Planning Agents:</strong> Criteria checks & actionable checklists.</li>'
            '<li><strong>Verification & Revision Agents:</strong> Fact-checks dates, fees & claims.</li>'
            '<li><strong>Recovery, Application Letter & Helpdesk Agents:</strong> Complete institutional support.</li>'
            '</ul></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="card"><h3>🔒 Security & Institutional Trust</h3>'
            '<ul style="color:#475569;font-size:.88rem;line-height:1.7">'
            '<li><strong>Role-Based Access Control:</strong> Student, Admin, and Helpdesk Officer roles enforced server-side.</li>'
            '<li><strong>Prompt-Injection Scanning:</strong> Uploaded PDFs are scanned before indexing.</li>'
            '<li><strong>No Fabricated Policies:</strong> Missing facts report clearly instead of guessing.</li>'
            '<li><strong>Multilingual Support:</strong> English, Tamil, Hindi, and Telugu.</li>'
            '</ul></div>',
            unsafe_allow_html=True,
        )

    ui.render_footer()
