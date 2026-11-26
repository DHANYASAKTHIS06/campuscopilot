"""AcadFlow — Student Dashboard"""
import datetime
import streamlit as st
import db
import ui


def show(user: dict):
    ui.render_chrome(
        user,
        "Student Home",
        "Your academic overview, deadlines, announcements, and quick actions.",
        breadcrumbs=["Student Home"],
    )

    uid = user["id"]
    display_name = user.get("full_name") or user.get("username")
    dept_info = f"{user.get('department') or 'Student'} · Sem {user.get('semester') or '—'}"

    st.markdown(
        f'<div class="af-hero">'
        f'<div><h1>Welcome back, {display_name} 👋</h1>'
        f'<p>{ui.BRAND_NAME} — {ui.BRAND_TAGLINE}</p></div>'
        f'<div class="af-hero-pill">🎓 {dept_info}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tasks = db.all_tasks(uid)
    tickets = db.get_tickets(user_id=uid)
    chats = db.get_chat_history(uid, limit=5)
    announcements = db.get_announcements(limit=4)
    docs = db.get_documents()
    indexed_docs = [d for d in docs if d.get("indexed")]

    done = sum(1 for t in tasks if t["status"] == "done")
    pending = sum(1 for t in tasks if t["status"] == "pending")
    today = datetime.date.today().isoformat()
    overdue = sum(1 for t in tasks if t.get("deadline") and t["deadline"][:10] < today and t["status"] != "done")
    open_tk = sum(1 for t in tickets if t["status"] in ("open", "in_progress"))
    pct = int(done / len(tasks) * 100) if tasks else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="stat-card blue"><div class="stat-label">📚 Indexed Documents</div>'
            f'<div class="stat-value">{len(indexed_docs)}</div>'
            f'<div class="stat-delta">Ready for AI search</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat-card violet"><div class="stat-label">✅ Pending Tasks</div>'
            f'<div class="stat-value">{pending}</div>'
            f'<div class="stat-delta" style="color:{"#EF4444" if overdue else "#10B981"}">'
            f'{f"⚠️ {overdue} overdue" if overdue else f"{done} completed ({pct}%)"}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat-card cyan"><div class="stat-label">🎫 Active Tickets</div>'
            f'<div class="stat-value">{open_tk}</div>'
            f'<div class="stat-delta">{len(tickets)} total submitted</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="stat-card green"><div class="stat-label">💬 Recent Queries</div>'
            f'<div class="stat-value">{len(chats)}</div>'
            f'<div class="stat-delta">Saved in history</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick-access feature cards ─────────────────────────────────────────
    st.markdown("### ⚡ Quick Access")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.markdown(
            '<div class="feature-card"><strong>✨ Ask AcadFlow</strong>'
            '<div style="font-size:.82rem;color:#475569;margin:.25rem 0 .6rem">'
            'Chat with institutional documents & get cited answers.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Open AI Chat →", key="qa_chat", type="primary", use_container_width=True):
            ui.navigate("chat")
    with q2:
        st.markdown(
            '<div class="feature-card violet"><strong>🎯 Eligibility Check</strong>'
            '<div style="font-size:.82rem;color:#475569;margin:.25rem 0 .6rem">'
            'Compare your profile against scholarship & program rules.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Check Eligibility →", key="qa_elig", use_container_width=True):
            ui.navigate("eligibility")
    with q3:
        st.markdown(
            '<div class="feature-card cyan"><strong>✅ Planning & Tasks</strong>'
            '<div style="font-size:.82rem;color:#475569;margin:.25rem 0 .6rem">'
            'Track deadlines, steps, and export calendar events.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("View Tasks →", key="qa_tasks", use_container_width=True):
            ui.navigate("tasks")
    with q4:
        st.markdown(
            '<div class="feature-card green"><strong>📝 Application Studio</strong>'
            '<div style="font-size:.82rem;color:#475569;margin:.25rem 0 .6rem">'
            'Draft formal letters and download formatted A4 PDFs.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Draft Letter →", key="qa_app", use_container_width=True):
            ui.navigate("application")

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1.35, 1])

    # ── Left: Deadlines + Recent Conversations ─────────────────────────────
    with left:
        with st.container(border=True):
            st.markdown("### 📅 Upcoming Deadlines & Tasks")
            upcoming = sorted(
                [t for t in tasks if t["status"] != "done"],
                key=lambda x: x.get("deadline") or "9999-99-99",
            )[:5]
            if not upcoming:
                st.markdown(
                    '<div class="cc-alert info"><span>💡</span>'
                    '<span>No pending tasks. Ask AcadFlow about an application to generate a checklist.</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                for t in upcoming:
                    dl = t.get("deadline", "")
                    is_over = dl and dl[:10] < today
                    st.markdown(
                        f'<div class="checklist-item">'
                        f'<div style="flex:1"><div style="font-size:.86rem;font-weight:600;color:#17233F">'
                        f'{"⚠️ " if is_over else ""}{t["step"]}</div>'
                        f'<div style="font-size:.76rem;color:#667085;margin-top:.15rem">'
                        f'{t["procedure"]} · {dl or "No deadline"}</div></div>'
                        f'{ui.status_badge(t["status"])}</div>',
                        unsafe_allow_html=True,
                    )

        with st.container(border=True):
            st.markdown("### 💬 Recent Conversations")
            if not chats:
                st.caption("No conversations yet. Start a chat with AcadFlow!")
            else:
                for ch in reversed(chats[-4:]):
                    st.markdown(
                        f'<div style="border-bottom:1px solid #F1F5F9;padding:.55rem 0">'
                        f'<div style="font-size:.85rem;font-weight:600;color:#17233F">Q: {ch["question"][:80]}</div>'
                        f'<div style="font-size:.78rem;color:#667085;margin-top:.15rem">'
                        f'{ch["answer"][:110]}{"..." if len(ch["answer"]) > 110 else ""}</div></div>',
                        unsafe_allow_html=True,
                    )

    # ── Right: Announcements + Tickets + Suggested Questions ───────────────
    with right:
        with st.container(border=True):
            st.markdown("### 📢 Institutional Announcements")
            if not announcements:
                st.caption("No announcements posted yet.")
            else:
                for ann in announcements:
                    st.markdown(
                        f'<div style="border-bottom:1px solid #F1F5F9;padding:.55rem 0">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center">'
                        f'<strong style="font-size:.86rem;color:#17233F">{ann["title"]}</strong>'
                        f'{ui.badge(ann.get("category","General"), "violet")}</div>'
                        f'<div style="font-size:.8rem;color:#667085;margin-top:.2rem">{ann["body"]}</div>'
                        f'<div style="font-size:.72rem;color:#94A3B8;margin-top:.15rem">{ann["created_at"][:10]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        with st.container(border=True):
            st.markdown("### 🎫 Recent Support Tickets")
            if not tickets:
                st.caption("No support tickets raised.")
            else:
                for tk in tickets[:3]:
                    resp = "✅ Replied" if tk.get("officer_response") else "⏳ Pending reply"
                    st.markdown(
                        f'<div style="border-bottom:1px solid #F1F5F9;padding:.5rem 0">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center">'
                        f'<span style="font-size:.84rem;font-weight:600">#{tk["id"]} {tk["subject"][:32]}</span>'
                        f'{ui.status_badge(tk["status"])}</div>'
                        f'<div style="font-size:.75rem;color:#667085">{resp}</div></div>',
                        unsafe_allow_html=True,
                    )

    with st.container(border=True):
        st.markdown("### 💡 Try Asking AcadFlow")
        suggestions = [
            "How do I apply for a bonafide certificate?",
            "What are the scholarship eligibility criteria?",
            "What are the hostel rules and fees?",
        ]
        scols = st.columns(3)
        for i, sq in enumerate(suggestions):
            with scols[i]:
                if st.button(f"✨ {sq}", key=f"dash_sq_{i}", use_container_width=True):
                    st.session_state["prefill_question"] = sq
                    ui.navigate("chat")

    ui.render_footer()
