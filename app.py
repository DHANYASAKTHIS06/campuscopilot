"""
AcadFlow — Main Application Entry Point
Multi-role, multi-page Streamlit application with URL query-param routing.
"""
try:
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except Exception:
    pass

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    if hasattr(st, "secrets"):
        for key in [
            "GEMINI_API_KEY", "GEMINI_MODEL",
            "DATABASE_PATH", "CHROMA_PERSIST_DIRECTORY", "DOCUMENT_STORAGE_PATH",
            "ADMIN_PASSWORD", "OFFICER_PASSWORD",
        ]:
            if key in st.secrets and not os.getenv(key):
                os.environ[key] = st.secrets[key]
except Exception:
    pass

import db
import ui

st.set_page_config(
    page_title="AcadFlow — Intelligence That Moves Academia Forward.",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "AcadFlow — Intelligence That Moves Academia Forward."},
)

db.init()

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "dashboard"
if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = None


def get_user():
    token = st.session_state.get("auth_token")
    if not token:
        return None
    return db.get_session(token)


user = get_user()

if not user:
    st.session_state["current_page"] = "login"
    import pages_login
    pages_login.show()
    st.stop()

role = user.get("role", "student")
st.session_state["user"] = user

# Sync route from URL query_params if present and valid for user's role
url_page = None
try:
    url_page = st.query_params.get("page")
except Exception:
    url_page = None

permitted = ui.get_permitted_pages(role)
page = st.session_state.get("current_page", "dashboard")

if url_page and url_page != page:
    if url_page in permitted:
        page = url_page
        st.session_state["current_page"] = page
    else:
        st.warning("⛔ That page is not available for your role. Redirected to your Dashboard.")
        page = "dashboard"
        st.session_state["current_page"] = "dashboard"
        try:
            st.query_params["page"] = "dashboard"
        except Exception:
            pass

if page not in permitted:
    page = "dashboard"
    st.session_state["current_page"] = "dashboard"

# ── Role-based Routing (enforced server-side) ─────────────────────────────────
if role == "student":
    if page == "dashboard":
        import pages_student
        pages_student.show(user)
    elif page == "chat":
        import pages_chat
        pages_chat.show(user)
    elif page == "tasks":
        import pages_tasks
        pages_tasks.show(user)
    elif page == "eligibility":
        import pages_eligibility
        pages_eligibility.show(user)
    elif page == "application":
        import pages_application
        pages_application.show(user)
    elif page == "helpdesk":
        import pages_helpdesk_student
        pages_helpdesk_student.show(user)
    elif page == "profile":
        import pages_profile
        pages_profile.show(user)
    elif page == "about":
        import pages_about
        pages_about.show(user)

elif role == "admin":
    if page in ("dashboard", "documents", "upload", "announcements", "students", "tickets", "settings"):
        import pages_admin
        pages_admin.show(user, section=page)
    elif page == "profile":
        import pages_profile
        pages_profile.show(user)
    elif page == "about":
        import pages_about
        pages_about.show(user)

elif role == "officer":
    if page in ("dashboard", "tickets"):
        import pages_officer
        pages_officer.show(user)
    elif page == "profile":
        import pages_profile
        pages_profile.show(user)
    elif page == "about":
        import pages_about
        pages_about.show(user)

else:
    st.error("Unknown role. Please contact the administrator.")
    if st.button("Sign Out"):
        ui.logout()
        st.rerun()
