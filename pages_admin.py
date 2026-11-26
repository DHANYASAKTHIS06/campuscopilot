"""AcadFlow — Admin Dashboard & Management Suite"""
import os
import streamlit as st
import agents
import db
import rag
import ui


def show(user: dict, section: str = "dashboard"):
    ui.inject_css()
    ui.render_sidebar(user)

    # Enforce admin authorization server-side
    if user.get("role") != "admin":
        st.error("⛔ Access denied. Administrator privileges required.")
        st.stop()

    stats = db.get_stats()
    ai_status = agents.get_ai_status()

    if section == "dashboard":
        _show_overview(user, stats, ai_status)
    elif section in ("documents", "upload"):
        _show_documents(user)
    elif section == "announcements":
        _show_announcements(user)
    elif section == "students":
        _show_students()
    elif section == "tickets":
        _show_tickets()
    elif section == "settings":
        _show_settings(ai_status, stats)
    else:
        _show_overview(user, stats, ai_status)

    ui.render_footer()


def _show_overview(user: dict, stats: dict, ai_status: dict):
    st.markdown(
        f'<div class="af-hero">'
        f'<div><h1>AcadFlow Admin Console</h1>'
        f'<p>Institutional documents, student accounts, announcements, and AI health.</p></div>'
        f'<div class="af-hero-pill">{"🟢 Gemini Ready" if ai_status["configured"] else "🔴 Gemini Not Configured"}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        ("blue",   "📄 Documents",      stats["total_documents"],   f"{stats['indexed_documents']} indexed"),
        ("violet", "🔢 Vector Chunks",  stats["total_chunks"],      f"ChromaDB live: {rag.count()}"),
        ("cyan",   "👥 Students",       stats["total_students"],    "Registered accounts"),
        ("amber",  "🎫 Open Tickets",   stats["open_tickets"],      f"{stats['total_tickets']} total"),
        ("green",  "🤖 AI Provider",    "Gemini",                   ai_status["model"]),
    ]
    for col, (accent, label, val, sub) in zip([c1, c2, c3, c4, c5], cards):
        with col:
            st.markdown(
                f'<div class="stat-card {accent}">'
                f'<div class="stat-label">{label}</div>'
                f'<div class="stat-value" style="font-size:1.55rem">{val}</div>'
                f'<div class="stat-delta">{sub}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1])

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📄 Recent Documents")
        docs = db.get_documents()[:5]
        if not docs:
            st.info("No documents uploaded yet. Open Document Manager to upload PDFs.")
        else:
            for d in docs:
                idx_b = ui.badge("Indexed", "green") if d.get("indexed") else ui.badge("Pending", "grey")
                sc_b = ui.status_badge(d.get("security_scan", "pending"))
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;'
                    f'padding:.55rem 0;border-bottom:1px solid #F1F5F9">'
                    f'<div><strong style="font-size:.86rem">{d["name"]}</strong>'
                    f'<div style="font-size:.75rem;color:#64748B">{d["page_count"]} pages · {d["chunk_count"]} chunks</div></div>'
                    f'<div style="display:flex;gap:.35rem">{sc_b}{idx_b}</div></div>',
                    unsafe_allow_html=True,
                )
        if st.button("Open Document Manager →", type="primary", use_container_width=True):
            st.session_state["current_page"] = "documents"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Admin Quick Actions")
        if st.button("⬆️ Upload & Index PDFs", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "documents"
            st.rerun()
        if st.button("📢 Post Announcement", use_container_width=True):
            st.session_state["current_page"] = "announcements"
            st.rerun()
        if st.button("👥 View Student Directory", use_container_width=True):
            st.session_state["current_page"] = "students"
            st.rerun()
        if st.button("⚙️ Check Gemini AI Status", use_container_width=True):
            st.session_state["current_page"] = "settings"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def _show_documents(user: dict):
    ui.page_header(
        "Document Manager",
        "Upload institutional PDFs, run prompt-injection scans, and manage ChromaDB + BM25 indexing.",
        section="Administration",
    )

    tab_list, tab_upload = st.tabs(["📚 Uploaded Documents", "⬆️ Upload & Index PDF"])

    with tab_list:
        search_q = st.text_input("🔍 Search documents", placeholder="Filter by filename...")
        docs = db.get_documents()
        if search_q.strip():
            docs = [d for d in docs if search_q.strip().lower() in d["name"].lower()]

        if not docs:
            st.info("No matching documents found.")
        else:
            for doc in docs:
                scan = doc.get("security_scan", "pending")
                scan_badge = ui.status_badge(
                    "safe" if scan == "safe" else ("unsafe" if scan == "unsafe" else "pending_scan")
                )
                indexed_badge = ui.badge("Indexed ✓", "green") if doc.get("indexed") else ui.badge("Not Indexed", "grey")
                st.markdown(
                    f'<div class="card" style="padding:1rem 1.2rem;margin-bottom:.55rem">'
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.5rem">'
                    f'<div><div style="font-weight:700;font-size:.92rem;color:#0F172A">📄 {doc["name"]}</div>'
                    f'<div style="font-size:.78rem;color:#64748B;margin-top:.2rem">'
                    f'{doc["page_count"]} pages · {doc["chunk_count"]} chunks · Uploaded {doc["uploaded_at"][:10]}'
                    f'</div></div>'
                    f'<div style="display:flex;gap:.45rem;align-items:center">{scan_badge}{indexed_badge}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                b1, b2, _ = st.columns([1, 1.3, 3.7])
                with b1:
                    if st.button("🗑 Remove", key=f"del_doc_{doc['name']}", use_container_width=True):
                        rag.delete_document(doc["name"])
                        db.delete_document(doc["name"])
                        fp = doc.get("file_path", "")
                        if fp and os.path.exists(fp):
                            try:
                                os.remove(fp)
                            except Exception:
                                pass
                        st.toast(f"Removed {doc['name']}", icon="🗑")
                        st.rerun()
                with b2:
                    if not doc.get("indexed") and doc.get("security_scan") != "unsafe":
                        if st.button("🔄 Index Now", key=f"reidx_{doc['name']}", use_container_width=True):
                            fp = doc.get("file_path", "")
                            if fp and os.path.exists(fp):
                                with open(fp, "rb") as fh:
                                    pages = rag.extract_pdf(fh.read())
                                if pages:
                                    cnt = rag.ingest(doc["name"], pages)
                                    db.update_document(doc["name"], indexed=True, chunk_count=cnt)
                                    st.success(f"Indexed {cnt} chunks.")
                                    st.rerun()
                            else:
                                st.error("PDF file missing on disk. Please re-upload.")

    with tab_upload:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Upload Institutional PDFs")
        st.caption("Upload handbooks, scholarship circulars, fee schedules, exam rules, and hostel policies (max 50 MB).")
        files = st.file_uploader("Select PDF files", type="pdf", accept_multiple_files=True)
        c1, c2 = st.columns(2)
        with c1:
            do_scan = st.checkbox("Run security scan (prompt-injection check)", value=True)
        with c2:
            do_index = st.checkbox("Index into ChromaDB + BM25 immediately", value=True)

        if files and st.button("⬆️ Upload & Process", type="primary", use_container_width=True):
            for f in files:
                if not f.name.lower().endswith(".pdf"):
                    st.error(f"❌ {f.name}: Only PDF files are allowed.")
                    continue
                if f.size > 50 * 1024 * 1024:
                    st.error(f"⚠️ {f.name}: Exceeds 50 MB limit.")
                    continue

                data = f.read()
                with st.spinner(f"Processing {f.name}..."):
                    file_path = rag.save_pdf(data, f.name)
                    pages = rag.extract_pdf(data)
                    if not pages:
                        st.warning(f"⚠️ {f.name}: No extractable text found.")
                        continue

                    all_text = "\n".join(t for _, t in pages)
                    scan_result = "not_checked"
                    if do_scan:
                        sr = rag.security_scan(all_text)
                        scan_result = "safe" if sr["safe"] else "unsafe"
                        if not sr["safe"]:
                            st.error(f"🚨 {f.name}: Quarantined — suspicious prompt-injection pattern detected.")
                            db.save_document(f.name, file_path, len(pages), 0, uploaded_by=user["id"])
                            db.update_document(f.name, security_scan="unsafe", indexed=False)
                            db.save_notice(f.name, all_text, uploaded_by=user["id"])
                            continue

                    old_text = db.get_notice(f.name)
                    if old_text and old_text != all_text:
                        diffs = rag.diff_text(old_text, all_text)
                        if diffs:
                            st.info(f"📢 {f.name}: Updated notice detected ({len(diffs)} line changes).")

                    db.save_notice(f.name, all_text, uploaded_by=user["id"])
                    db.save_document(f.name, file_path, len(pages), 0, uploaded_by=user["id"])
                    db.update_document(f.name, security_scan=scan_result)

                    if do_index:
                        cnt = rag.ingest(f.name, pages)
                        db.update_document(f.name, indexed=True, chunk_count=cnt)
                        st.success(f"✅ {f.name}: {cnt} chunks indexed across {len(pages)} page(s).")
                    else:
                        st.success(f"✅ {f.name}: Saved ({len(pages)} pages). Ready to index.")
        st.markdown("</div>", unsafe_allow_html=True)


def _show_announcements(user: dict):
    ui.page_header(
        "Institutional Announcements",
        "Publish official notices visible on all Student Dashboards.",
        section="Administration",
    )

    with st.form("ann_form", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            title = st.text_input("Announcement Title *", placeholder="e.g. Merit Scholarship Deadline Extended")
        with c2:
            category = st.selectbox("Category", ["General", "Scholarship", "Examination", "Fees", "Hostel"])
        body = st.text_area("Details *", placeholder="Write the announcement details for students...", height=100)
        if st.form_submit_button("📢 Publish Announcement", type="primary"):
            if not title.strip() or not body.strip():
                st.error("Title and details are required.")
            else:
                db.create_announcement(title, body, category, created_by=user["id"])
                st.toast("Announcement published!", icon="📢")
                st.rerun()

    st.markdown("### Published Announcements")
    anns = db.get_announcements(limit=30)
    if not anns:
        st.info("No announcements published yet.")
    for a in anns:
        c1, c2 = st.columns([6, 1])
        with c1:
            st.markdown(
                f'<div class="card" style="padding:.9rem 1.1rem;margin-bottom:.5rem">'
                f'<div style="display:flex;justify-content:space-between">'
                f'<strong>{a["title"]}</strong>{ui.badge(a["category"], "violet")}</div>'
                f'<div style="font-size:.85rem;color:#475569;margin:.3rem 0">{a["body"]}</div>'
                f'<div style="font-size:.73rem;color:#94A3B8">{a["created_at"][:16]}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("🗑", key=f"del_ann_{a['id']}", help="Delete announcement"):
                db.delete_announcement(a["id"])
                st.rerun()


def _show_students():
    ui.page_header(
        "Student Directory",
        "View registered student accounts and academic profiles.",
        section="Administration",
    )
    students = db.get_all_users(role="student")
    q = st.text_input("🔍 Search students", placeholder="Search by name, username, or department...")
    if q.strip():
        ql = q.strip().lower()
        students = [
            s for s in students
            if ql in (s.get("full_name") or "").lower()
            or ql in s["username"].lower()
            or ql in (s.get("department") or "").lower()
        ]

    st.caption(f"Showing {len(students)} student(s)")
    if not students:
        st.info("No students match your filter.")
        return

    page_size = 15
    total_pages = max(1, (len(students) + page_size - 1) // page_size)
    page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1) if total_pages > 1 else 1
    chunk = students[(page_num - 1) * page_size : page_num * page_size]

    rows_html = ""
    for s in chunk:
        rows_html += (
            f"<tr><td>{s.get('full_name') or '—'}</td>"
            f"<td><code>{s['username']}</code></td>"
            f"<td>{s.get('email') or '—'}</td>"
            f"<td>{s.get('department') or '—'}</td>"
            f"<td>{s.get('semester') or '—'}</td>"
            f"<td>{s.get('cgpa') or '—'}</td>"
            f"<td>{s.get('created_at','')[:10]}</td></tr>"
        )
    st.markdown(
        '<div class="card" style="overflow-x:auto"><table class="cc-table">'
        '<thead><tr><th>Name</th><th>Username</th><th>Email</th><th>Dept</th>'
        '<th>Sem</th><th>CGPA</th><th>Joined</th></tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def _show_tickets():
    ui.page_header(
        "Helpdesk Tickets Overview",
        "Monitor all student support tickets across the institution.",
        section="Administration",
    )
    tickets = db.get_tickets()
    status_filter = st.selectbox("Filter by status", ["All", "Open", "In Progress", "Resolved", "Closed"])
    if status_filter != "All":
        tickets = [t for t in tickets if t["status"].replace("_", " ").title() == status_filter]

    if not tickets:
        st.info("No tickets found.")
        return

    for t in tickets:
        st.markdown(
            f'<div class="ticket-card">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<div><strong>#{t["id"]} — {t["subject"]}</strong>'
            f'<span style="margin-left:.65rem;font-size:.8rem;color:#64748B">'
            f'by {t.get("student_name") or t.get("student_username","?")} ({t.get("department","")})</span></div>'
            f'{ui.status_badge(t["status"])}</div>'
            f'<div style="font-size:.84rem;color:#334155;margin-top:.4rem">{t.get("description","")[:160]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _show_settings(ai_status: dict, stats: dict):
    ui.page_header(
        "AI & System Status",
        "Inspect Google Gemini configuration, vector index health, and storage paths.",
        section="Administration",
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🤖 Google Gemini Status")
        st.markdown(f"- **Provider:** `{ai_status['provider']}`")
        st.markdown(f"- **Model (`GEMINI_MODEL`):** `{ai_status['model']}`")
        if ai_status["configured"]:
            st.success("✅ `GEMINI_API_KEY` is configured on the server.")
        else:
            st.error("❌ `GEMINI_API_KEY` is NOT configured. Set it in Render Environment.")
        st.caption("API keys are stored server-side only and are never exposed in the UI.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 💾 Storage & Index Health")
        st.markdown(f"- **Database (`DATABASE_PATH`):** `{db.DB}`")
        st.markdown(f"- **Vector Store (`CHROMA_PERSIST_DIRECTORY`):** `{rag.CHROMA_PATH}`")
        st.markdown(f"- **PDF Storage (`DOCUMENT_STORAGE_PATH`):** `{rag.UPLOAD_PATH}`")
        st.markdown(f"- **Live ChromaDB Chunks:** `{rag.count()}`")
        st.markdown(f"- **Tracked Documents:** `{stats['total_documents']}` ({stats['indexed_documents']} indexed)")
        st.markdown("</div>", unsafe_allow_html=True)
