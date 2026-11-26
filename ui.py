"""
AcadFlow — Shared UI Utilities
Design system injection, AcadFlow logo, navigation sidebar, breadcrumbs, and renderers.
"""
import os
import re
import datetime
import streamlit as st

BRAND_NAME = "AcadFlow"
BRAND_TAGLINE = "Intelligence That Moves Academia Forward."
BRAND_DESC = (
    "AcadFlow is an AI-powered institutional intelligence platform that simplifies "
    "academic information, document intelligence, eligibility assessment, planning, "
    "and institutional support."
)

LOGO_SVG = (
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" '
    'xmlns="http://www.w3.org/2000/svg">'
    '<path d="M12 3L2 8.5L12 14L22 8.5L12 3Z" fill="white" fill-opacity="0.95"/>'
    '<path d="M6 11.5V16.5C6 18.433 8.686 20 12 20C15.314 20 18 18.433 18 16.5V11.5L12 14.8L6 11.5Z" '
    'fill="white" fill-opacity="0.8"/>'
    '<circle cx="20" cy="14" r="1.5" fill="#67E8F9"/>'
    '</svg>'
)


# ─── CSS injection ──────────────────────────────────────────────────────────────
def inject_css():
    css_path = os.path.join(os.path.dirname(__file__), ".streamlit", "style.css")
    css = ""
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as f:
            css = f.read()
    extra = (
        'div[data-testid="stTabs"] button{font-size:.88rem!important;font-weight:600!important;color:#475569!important;}'
        'div[data-testid="stTabs"] button[aria-selected="true"]{color:#2563EB!important;font-weight:700!important;}'
        '.stSpinner>div{border-top-color:#2563EB!important;}'
        'div[data-testid="stMetricValue"]{font-size:1.6rem!important;font-weight:800!important;}'
    )
    st.markdown(f"<style>{css}\n{extra}</style>", unsafe_allow_html=True)


# ─── Auth helpers ───────────────────────────────────────────────────────────────
def get_current_user() -> dict | None:
    token = st.session_state.get("auth_token")
    if not token:
        return None
    import db
    user = db.get_session(token)
    if user:
        st.session_state["user"] = user
    return user


def require_auth(role=None):
    user = get_current_user()
    if not user:
        st.session_state["current_page"] = "login"
        st.rerun()
    if role and isinstance(role, str) and user.get("role") != role:
        st.error("⛔ Access denied. You do not have permission to view this page.")
        st.stop()
    if role and isinstance(role, (list, tuple)) and user.get("role") not in role:
        st.error("⛔ Access denied. You do not have permission to view this page.")
        st.stop()
    return user


def logout():
    import db
    token = st.session_state.pop("auth_token", None)
    if token:
        db.delete_session(token)
    st.session_state.pop("user", None)
    st.session_state.pop("chat_messages", None)
    st.session_state["current_page"] = "login"


# ─── Sidebar navigation ─────────────────────────────────────────────────────────
def render_sidebar(user: dict):
    role = user.get("role", "student")
    name = user.get("full_name") or user.get("username", "")

    with st.sidebar:
        st.markdown(
            f'<div class="sidebar-logo">'
            f'<div class="sidebar-logo-icon">{LOGO_SVG}</div>'
            f'<div class="sidebar-logo-text">'
            f'<h2>{BRAND_NAME}</h2>'
            f'<p>Academic Intelligence</p>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        current = st.session_state.get("current_page", "dashboard")

        def nav(icon: str, label: str, page: str):
            is_active = current == page
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["current_page"] = page
                st.rerun()

        if role == "student":
            st.markdown('<p class="nav-section-label">Workspace</p>', unsafe_allow_html=True)
            nav("🏠", "Dashboard",          "dashboard")
            nav("✨", "Ask AcadFlow",       "chat")
            nav("🎯", "Eligibility Check",  "eligibility")
            nav("✅", "Planning & Tasks",   "tasks")
            nav("📝", "Application Studio", "application")
            st.markdown('<p class="nav-section-label">Support & Info</p>', unsafe_allow_html=True)
            nav("🎫", "Helpdesk Support",   "helpdesk")
            nav("👤", "My Profile",         "profile")
            nav("ℹ️", "About AcadFlow",     "about")

        elif role == "admin":
            st.markdown('<p class="nav-section-label">Administration</p>', unsafe_allow_html=True)
            nav("🏠", "Admin Overview",     "dashboard")
            nav("📄", "Document Manager",   "documents")
            nav("📢", "Announcements",      "announcements")
            nav("👥", "Student Directory",  "students")
            nav("🎫", "Helpdesk Tickets",   "tickets")
            nav("⚙️", "AI & System Status", "settings")
            st.markdown('<p class="nav-section-label">Account</p>', unsafe_allow_html=True)
            nav("👤", "My Profile",         "profile")
            nav("ℹ️", "About AcadFlow",     "about")

        elif role == "officer":
            st.markdown('<p class="nav-section-label">Helpdesk</p>', unsafe_allow_html=True)
            nav("🏠", "Officer Dashboard",  "dashboard")
            nav("🎫", "Manage Tickets",     "tickets")
            st.markdown('<p class="nav-section-label">Account</p>', unsafe_allow_html=True)
            nav("👤", "My Profile",         "profile")
            nav("ℹ️", "About AcadFlow",     "about")

        initials = "".join(w[0].upper() for w in name.split()[:2]) or name[:2].upper()
        role_label = {
            "student": "Student",
            "admin": "Administrator",
            "officer": "Helpdesk Officer",
        }.get(role, role.title())

        st.markdown(
            f'<div class="sidebar-user">'
            f'<div class="sidebar-user-card">'
            f'<div class="sidebar-avatar">{initials}</div>'
            f'<div class="sidebar-user-info">'
            f'<p class="sidebar-user-name">{name}</p>'
            f'<p class="sidebar-user-role">{role_label}</p>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("")
        if st.button("🚪  Sign Out", use_container_width=True):
            logout()
            st.rerun()


# ─── Layout & component helpers ─────────────────────────────────────────────────
def page_header(title: str, subtitle: str = "", section: str = "AcadFlow"):
    st.markdown(
        f'<div class="af-breadcrumb">{section} / <span>{title}</span></div>'
        f'<div class="page-header">'
        f'<h1>{title}</h1>'
        f'{"<p>" + subtitle + "</p>" if subtitle else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        f'<div class="af-footer">'
        f'<span><strong>{BRAND_NAME}</strong> — {BRAND_TAGLINE}</span>'
        f'<span>Powered by Google Gemini & Hybrid RAG</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def badge(text: str, color: str = "blue") -> str:
    return f'<span class="badge badge-{color}">{text}</span>'


def status_badge(status: str) -> str:
    colors = {
        "open": "blue",
        "in_progress": "yellow",
        "resolved": "green",
        "closed": "grey",
        "pending": "yellow",
        "done": "green",
        "blocked": "red",
        "safe": "green",
        "unsafe": "red",
        "pending_scan": "yellow",
        "not_checked": "grey",
    }
    return badge(status.replace("_", " ").title(), colors.get(status, "grey"))


def render_chat_message(role: str, content: str, timestamp: str = ""):
    if role == "user":
        initials = st.session_state.get("user", {}).get("full_name", "U")
        initials = "".join(w[0].upper() for w in initials.split()[:2]) or "U"
        safe_content = content.replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(
            f'<div class="chat-msg user">'
            f'<div class="chat-avatar user-av">{initials}</div>'
            f'<div><div class="chat-bubble user">{safe_content}</div>'
            f'{"<div class=\'chat-time\'>" + timestamp + "</div>" if timestamp else ""}'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    else:
        formatted = content.replace("<", "&lt;").replace(">", "&gt;")
        formatted = re.sub(r'\[(\d+)\]', r'<span class="citation">[\1]</span>', formatted)
        formatted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', formatted)
        formatted = formatted.replace("\n", "<br>")
        st.markdown(
            f'<div class="chat-msg">'
            f'<div class="chat-avatar ai-av">✨</div>'
            f'<div><div class="chat-bubble ai">{formatted}</div>'
            f'{"<div class=\'chat-time\'>" + timestamp + "</div>" if timestamp else ""}'
            f'</div></div>',
            unsafe_allow_html=True,
        )


def render_eligibility(elig: dict):
    if not elig:
        return
    met = elig.get("met", [])
    not_met = elig.get("not_met", [])
    missing = elig.get("missing", [])
    summary = elig.get("summary", "")
    can_app = elig.get("can_apply", False)

    if summary:
        color = "success" if can_app else "warning"
        icon = "✅" if can_app else "⚠️"
        st.markdown(
            f'<div class="cc-alert {color}" style="margin-bottom:1rem">'
            f'<span style="font-size:1.1rem">{icon}</span>'
            f'<span><strong>Assessment:</strong> {summary}</span></div>',
            unsafe_allow_html=True,
        )

    if met:
        items = "".join(f'<div class="elig-item"><span style="color:#10B981">✓</span> {m}</div>' for m in met)
        st.markdown(
            f'<div class="elig-section elig-met">'
            f'<div class="elig-header">✅ Criteria Met ({len(met)})</div>'
            f'<div class="elig-body">{items}</div></div>',
            unsafe_allow_html=True,
        )
    if not_met:
        items = "".join(f'<div class="elig-item"><span style="color:#EF4444">✗</span> {m}</div>' for m in not_met)
        st.markdown(
            f'<div class="elig-section elig-notmet">'
            f'<div class="elig-header">❌ Criteria Not Met ({len(not_met)})</div>'
            f'<div class="elig-body">{items}</div></div>',
            unsafe_allow_html=True,
        )
    if missing:
        items = "".join(f'<div class="elig-item"><span style="color:#F59E0B">?</span> {m}</div>' for m in missing)
        st.markdown(
            f'<div class="elig-section elig-miss">'
            f'<div class="elig-header">❓ Missing Information ({len(missing)})</div>'
            f'<div class="elig-body">{items}</div></div>',
            unsafe_allow_html=True,
        )


def render_sources(chunks: list[dict]):
    if not chunks:
        return
    seen = []
    for c in chunks:
        label = f"{c['source']}, Page {c['page']}"
        if label not in seen:
            seen.append(label)
    st.markdown(
        '<div style="font-size:.8rem;color:#475569;margin:.35rem 0 .4rem">'
        '<strong>Source:</strong> ' + " &nbsp;|&nbsp; ".join(seen[:4]) +
        '</div>',
        unsafe_allow_html=True,
    )
    with st.expander(f"📚 View Document Citations ({len(chunks)} references)"):
        for i, c in enumerate(chunks, 1):
            st.markdown(
                f'<div class="card-sm" style="margin-bottom:.5rem">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:.35rem">'
                f'<span class="badge badge-violet">[{i}]</span>'
                f'<span style="font-size:.78rem;color:#475569">📄 {c["source"]} · Page {c["page"]}</span>'
                f'</div>'
                f'<p style="font-size:.82rem;color:#334155;margin:0;line-height:1.5">'
                f'{c["text"][:320]}{"..." if len(c["text"]) > 320 else ""}'
                f'</p></div>',
                unsafe_allow_html=True,
            )


def render_verification(ver: dict):
    if not ver:
        return
    verified = ver.get("verified", True)
    issues = ver.get("issues", [])
    summary = ver.get("summary", "")
    if verified:
        st.markdown(
            f'<div class="cc-alert success"><span>✅</span>'
            f'<span><strong>Verified:</strong> {summary}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        issue_html = "".join(f"<li>{i}</li>" for i in issues)
        st.markdown(
            f'<div class="cc-alert warning"><span>⚠️</span><div>'
            f'<strong>Verification Notes:</strong> {summary}'
            f'<ul style="margin:.45rem 0 0;padding-left:1.25rem;font-size:.84rem">{issue_html}</ul>'
            f'</div></div>',
            unsafe_allow_html=True,
        )


def render_plan(plan: dict, user_id=None):
    if not plan or not plan.get("steps"):
        return
    import db
    st.markdown(
        f'<h3 style="font-size:1.05rem;font-weight:700;color:#0F172A;margin:.5rem 0">'
        f'📋 Checklist: {plan.get("procedure", "Application Steps")}</h3>',
        unsafe_allow_html=True,
    )
    docs = plan.get("documents", [])
    if docs:
        st.markdown("**📁 Required Documents**")
        for d in docs:
            st.markdown(f"- {d}")

    today = datetime.date.today().isoformat()
    steps = plan.get("steps", [])
    for i, s in enumerate(steps, 1):
        dl = s.get("deadline") or ""
        overdue = dl and dl[:10] < today
        icon = "⚠️" if overdue else f"{i}."
        color = "#EF4444" if overdue else "#2563EB"
        st.markdown(
            f'<div class="checklist-item">'
            f'<div style="font-size:.85rem;font-weight:700;color:{color};min-width:1.5rem">{icon}</div>'
            f'<div style="flex:1">'
            f'<div style="font-size:.88rem;font-weight:600;color:#0F172A">{s.get("step","")}</div>'
            f'<div style="font-size:.77rem;color:#475569;margin-top:.2rem">'
            f'{("📅 " + dl) if dl else "No deadline stated"}'
            f'{(" · " + s.get("source","")) if s.get("source") else ""}'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

    if user_id:
        st.markdown("")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save to Planning & Tasks", type="primary", use_container_width=True):
                db.add_tasks(user_id, plan.get("procedure", ""), steps)
                st.toast("Tasks saved to Planning & Tasks!", icon="✅")
                st.success("✅ Saved to Planning & Tasks!")
        with col2:
            ics_events = []
            for s in steps:
                dl = s.get("deadline")
                if dl:
                    try:
                        dt = datetime.date.fromisoformat(dl[:10])
                        dtstr = dt.strftime("%Y%m%d")
                        ics_events.append(
                            f"BEGIN:VEVENT\r\nSUMMARY:{s.get('step','Task')}\r\n"
                            f"DTSTART;VALUE=DATE:{dtstr}\r\nDTEND;VALUE=DATE:{dtstr}\r\n"
                            f"DESCRIPTION:{plan.get('procedure','')}\r\nEND:VEVENT"
                        )
                    except Exception:
                        pass
            if ics_events:
                ics = (
                    "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//AcadFlow//EN\r\n"
                    + "\r\n".join(ics_events)
                    + "\r\nEND:VCALENDAR"
                )
                st.download_button(
                    "📅 Export Calendar (.ics)",
                    data=ics.encode(),
                    file_name="acadflow_tasks.ics",
                    mime="text/calendar",
                    use_container_width=True,
                )
