"""AcadFlow — Admin Dashboard & Management Suite"""
import os
import streamlit as st
import agents
import db
import rag
import ui


def show(user: dict, section: str = "dashboard"):
    if user.get("role") != "admin":
        st.error("⛔ Access denied. Administrator privileges required.")
        st.stop()

    stats = db.get_stats()
    ai_status = agents.get_ai_status()

    if section == "dashboard":
        ui.render_chrome(
            user,
            "Admin Home",
            "Institutional documents, users, helpdesk activity, and Gemini AI status.",
            breadcrumbs=["Admin Home"],
        )
        _show_overview(user, stats, ai_status)
    elif section == "documents":
        ui.render_chrome(
            user,
            "Document Manager",
            "Inspect, search, re-index, or remove institutional PDFs.",
            breadcrumbs=["Admin Home", "Documents"],
        )
        _show_documents()
    elif section == "upload":
        ui.render_chrome(
            user,
            "Upload Document",
            "Upload institutional PDFs, run security scans, and index into ChromaDB + BM25.",
            breadcrumbs=["Admin Home", "Documents", "Upload Document"],
        )
        _show_upload(user)
    elif section == "announcements":
        ui.render_chrome(
            user,
            "Announcements",
            "Publish official institutional notices visible on all Student Dashboards.",
            breadcrumbs=["Admin Home", "Announcements"],
        )
        _show_announcements(user)
    elif section == "students":
        ui.render_chrome(
            user,
            "User Management",
            "Search and inspect registered student accounts.",
            breadcrumbs=["Admin Home", "User Management"],
        )
        _show_students()
    elif section == "tickets":
        ui.render_chrome(
            user,
            "Helpdesk Tickets",
            "Monitor all student support requests across the institution.",
            breadcrumbs=["Admin Home", "Helpdesk Tickets"],
        )
        _show_tickets()
    elif section == "settings":
        ui.render_chrome(
            user,
            "System & AI Status",
            "Inspect Google Gemini configuration, vector index health, and storage paths.",
            breadcrumbs=["Admin Home", "System & AI Status"],
        )
        _show_settings(ai_status, stats)
    else:
        ui.render_chrome(user, "Admin Home", breadcrumbs=["Admin Home"])
        _show_overview(user, stats, ai_status)

    ui.render_footer()


def _show_overview(user: dict, stats: dict, ai_status: dict):
    pill = "🟢 Gemini Ready" if ai_status["configured"] else "🔴 Gemini Not Configured"
    st.markdown(
        f'<div class="af-hero">'
        f'<div><h1>AcadFlow Admin Console</h1>'
        f'<p>Manage institutional knowledge, announcements, users, and AI health.</p></div>'
        f'<div class="af-hero-pill">{pill}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        ("blue",   "📄 Documents",      stats["total_documents"],   f"{stats['indexed_documents']} indexed"),
        ("violet", "🔢 Vector Chunks",  stats["total_chunks"],      f"Live in Chroma: {rag.count()}"),
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
    left, right = st.columns([1.25, 1])

    with left:
        with st.container(border=True):
            st.markdown("### 📄 Recently Uploaded Documents")
            docs = db.get_documents()[:5]
            if not docs:
                st.info("No documents uploaded yet. Click Upload Document to add your first institutional PDF.")
            else:
                for d in docs:
                    idx_b = ui.badge("Indexed", "green") if d.get("indexed") else ui.badge("Pending", "grey")
                    sc_b = ui.status_badge(d.get("security_scan", "pending"))
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;align-items:center;'
                        f'padding:.55rem 0;border-bottom:1px solid #F1F5F9">'
                        f'<div><strong style="font-size:.86rem">{d["name"]}</strong>'
                        f'<div style="font-size:.75rem;color:#667085">{d["page_count"]} pages · {d["chunk_count"]} chunks</div></div>'
                        f'<div style="display:flex;gap:.35rem">{sc_b}{idx_b}</div></div>',
                        unsafe_allow_html=True,
                    )
            b1, b2 = st.columns(2)
            with b1:
                if st.button("📄 Document Manager →", use_container_width=True):
                    ui.navigate("documents")
            with b2:
                if st.button("⬆️ Upload Document →", type="primary", use_container_width=True):
                    ui.navigate("upload")

    with right:
        with st.container(border=True):
            st.markdown("### ⚡ Quick Actions")
            if st.button("⬆️ Upload New PDF Document", key="adm_qa_up", use_container_width=True, type="primary"):
                ui.navigate("upload")
            if st.button("📢 Manage Announcements", key="adm_qa_ann", use_container_width=True):
                ui.navigate("announcements")
            if st.button("👥 Student Directory", key="adm_qa_stu", use_container_width=True):
                ui.navigate("students")
            if st.button("🎫 Review Helpdesk Tickets", key="adm_qa_tkt", use_container_width=True):
                ui.navigate("tickets")
            if st.button("⚙️ AI & System Health", key="adm_qa_set", use_container_width=True):
                ui.navigate("settings")


def _show_documents():
    c_search, c_btn = st.columns([3, 1])
    with c_search:
        search_q = st.text_input("🔍 Search documents", placeholder="Filter by filename...", label_visibility="collapsed")
    with c_btn:
        if st.button("⬆️ Upload New PDF", type="primary", use_container_width=True):
            ui.navigate("upload")

    docs = db.get_documents()
    if search_q.strip():
        docs = [d for d in docs if search_q.strip().lower() in d["name"].lower()]

    if not docs:
        st.markdown(
            '<div class="card" style="text-align:center;padding:2rem">'
            '<div style="font-size:2rem;margin-bottom:.5rem">📂</div>'
            '<strong>No documents found</strong>'
            '<p style="color:#64748B;font-size:.86rem">Upload institutional PDFs to power AcadFlow RAG answers.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    for doc in docs:
        dname = doc["name"]
        scan = doc.get("security_scan", "pending")
        scan_badge = ui.status_badge("safe" if scan == "safe" else ("unsafe" if scan == "unsafe" else "pending_scan"))
        indexed_badge = ui.badge("Indexed ✓", "green") if doc.get("indexed") else ui.badge("Not Indexed", "grey")
        st.markdown(
            f'<div class="card" style="padding:1rem 1.2rem;margin-bottom:.55rem">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.5rem">'
            f'<div><div style="font-weight:700;font-size:.92rem;color:#0F172A">📄 {dname}</div>'
            f'<div style="font-size:.78rem;color:#64748B;margin-top:.2rem">'
            f'{doc["page_count"]} pages · {doc["chunk_count"]} chunks · Uploaded {doc["uploaded_at"][:10]}'
            f'</div></div>'
            f'<div style="display:flex;gap:.45rem;align-items:center">{scan_badge}{indexed_badge}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        confirm_key = f"confirm_del_{dname}"
        b1, b2, _ = st.columns([1.4, 1.4, 3.2])
        with b1:
            if st.session_state.get(confirm_key):
                if st.button("⚠️ Confirm Delete", key=f"cf_del_{dname}", type="primary", use_container_width=True):
                    rag.delete_document(dname)
                    db.delete_document(dname)
                    fp = doc.get("file_path", "")
                    if fp and os.path.exists(fp):
                        try:
                            os.remove(fp)
                        except Exception:
                            pass
                    st.session_state.pop(confirm_key, None)
                    st.toast(f"Deleted {dname}", icon="🗑")
                    st.rerun()
            else:
                if st.button("🗑 Remove", key=f"del_doc_{dname}", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()
        with b2:
            if st.session_state.get(confirm_key):
                if st.button("Cancel", key=f"cancel_del_{dname}", use_container_width=True):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
            elif not doc.get("indexed") and doc.get("security_scan") != "unsafe":
                if st.button("🔄 Index Now", key=f"reidx_{dname}", use_container_width=True):
                    fp = doc.get("file_path", "")
                    if fp and os.path.exists(fp):
                        with open(fp, "rb") as fh:
                            pages = rag.extract_pdf(fh.read())
                        if pages:
                            cnt = rag.ingest(dname, pages)
                            if cnt > 0:
                                db.update_document(dname, indexed=True, chunk_count=cnt)
                                st.toast(f"Indexed {cnt} chunks.", icon="✅")
                                st.rerun()
                            else:
                                st.error("Indexing produced 0 chunks.")
                    else:
                        st.error("PDF file missing on disk. Please re-upload.")


def _show_upload(user: dict):
    with st.container(border=True):
        st.markdown("### ⬆️ Upload Institutional PDFs")
        st.markdown(
            '<div style="font-size:.85rem;color:#667085;margin-bottom:.75rem">'
            'Accepted format: <strong>PDF</strong> · Maximum size: <strong>50 MB per file</strong> · '
            'Automatically extracts text, scans for prompt injections, and indexes into ChromaDB + BM25.'
            '</div>',
            unsafe_allow_html=True,
        )

        uploader_key = f"pdf_uploader_{st.session_state.get('upload_nonce', 0)}"
        files = st.file_uploader(
            "Drag and drop PDF files here or click Browse files",
            type="pdf",
            accept_multiple_files=True,
            key=uploader_key,
        )

        if files:
            st.markdown("**Selected Files:**")
            for f in files:
                size_kb = round(f.size / 1024, 1)
                size_label = f"{round(size_kb / 1024, 2)} MB" if size_kb >= 1024 else f"{size_kb} KB"
                st.markdown(f"- 📄 **{f.name}** ({size_label})")

        c1, c2 = st.columns(2)
        with c1:
            do_scan = st.checkbox("Run security scan (prompt-injection check)", value=True)
        with c2:
            do_index = st.checkbox("Index into ChromaDB + BM25 immediately", value=True)

        if files and st.button("🚀 Upload & Process Documents", type="primary", use_container_width=True):
            progress = st.progress(0, text="Starting upload...")
            results = []
            total = len(files)

            for idx, f in enumerate(files, 1):
                base_pct = int(((idx - 1) / total) * 100)
                if not f.name.lower().endswith(".pdf"):
                    results.append(("error", f"{f.name}: Only PDF files are allowed."))
                    continue
                if f.size > 50 * 1024 * 1024:
                    results.append(("error", f"{f.name}: Exceeds 50 MB size limit."))
                    continue

                try:
                    progress.progress(min(base_pct + 20, 95), text=f"Extracting text from {f.name}...")
                    data = f.read()
                    file_path = rag.save_pdf(data, f.name)
                    pages = rag.extract_pdf(data)
                    if not pages:
                        results.append(("warning", f"{f.name}: No extractable text found in PDF."))
                        continue

                    all_text = "\n".join(t for _, t in pages)
                    scan_result = "not_checked"
                    if do_scan:
                        progress.progress(min(base_pct + 45, 95), text=f"Scanning {f.name} for prompt injections...")
                        sr = rag.security_scan(all_text)
                        scan_result = "safe" if sr["safe"] else "unsafe"
                        if not sr["safe"]:
                            db.save_document(f.name, file_path, len(pages), 0, uploaded_by=user["id"])
                            db.update_document(f.name, security_scan="unsafe", indexed=False)
                            db.save_notice(f.name, all_text, uploaded_by=user["id"])
                            results.append(("error", f"{f.name}: Quarantined — suspicious prompt-injection pattern detected."))
                            continue

                    db.save_notice(f.name, all_text, uploaded_by=user["id"])
                    db.save_document(f.name, file_path, len(pages), 0, uploaded_by=user["id"])
                    db.update_document(f.name, security_scan=scan_result)

                    if do_index:
                        progress.progress(min(base_pct + 75, 95), text=f"Indexing {f.name} into ChromaDB + BM25...")
                        cnt = rag.ingest(f.name, pages)
                        if cnt > 0:
                            db.update_document(f.name, indexed=True, chunk_count=cnt)
                            results.append(("success", f"{f.name}: {cnt} chunks indexed across {len(pages)} page(s)."))
                        else:
                            db.update_document(f.name, indexed=False, chunk_count=0)
                            results.append(("error", f"{f.name}: Indexing failed (0 chunks created)."))
                    else:
                        results.append(("success", f"{f.name}: Saved ({len(pages)} pages). Ready for indexing."))
                except Exception as e:
                    results.append(("error", f"{f.name}: Processing failed — {e}"))

            progress.progress(100, text="Processing complete.")
            st.session_state["last_upload_results"] = results
            st.toast("Document processing finished.", icon="📄")

        if st.session_state.get("last_upload_results"):
            st.markdown("---")
            st.markdown("### Processing Summary")
            for kind, msg in st.session_state["last_upload_results"]:
                if kind == "success":
                    st.success(f"✅ {msg}")
                elif kind == "warning":
                    st.warning(f"⚠️ {msg}")
                else:
                    st.error(f"❌ {msg}")

            st.markdown("#### What would you like to do next?")
            n1, n2, n3 = st.columns(3)
            with n1:
                if st.button("📄 View Documents", key="post_up_docs", type="primary", use_container_width=True):
                    st.session_state.pop("last_upload_results", None)
                    ui.navigate("documents")
            with n2:
                if st.button("⬆️ Upload Another Document", key="post_up_more", use_container_width=True):
                    st.session_state.pop("last_upload_results", None)
                    st.session_state["upload_nonce"] = st.session_state.get("upload_nonce", 0) + 1
                    st.rerun()
            with n3:
                if st.button("🏠 Go to Admin Dashboard", key="post_up_home", use_container_width=True):
                    st.session_state.pop("last_upload_results", None)
                    ui.navigate("dashboard")


def _show_announcements(user: dict):
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
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("### 🤖 Google Gemini Status")
            st.markdown(f"- **Provider:** `{ai_status['provider']}`")
            st.markdown(f"- **Model (`GEMINI_MODEL`):** `{ai_status['model']}`")
            if ai_status["configured"]:
                st.success("✅ `GEMINI_API_KEY` is configured on the server.")
            else:
                st.error("❌ `GEMINI_API_KEY` is NOT configured. Set it in Render Environment.")
            st.caption("API keys are stored server-side only and are never exposed in the UI.")

    with c2:
        with st.container(border=True):
            st.markdown("### 💾 Storage & Index Health")
            st.markdown(f"- **Database (`DATABASE_PATH`):** `{db.DB}`")
            st.markdown(f"- **Vector Store (`CHROMA_PERSIST_DIRECTORY`):** `{rag.CHROMA_PATH}`")
            st.markdown(f"- **PDF Storage (`DOCUMENT_STORAGE_PATH`):** `{rag.UPLOAD_PATH}`")
            st.markdown(f"- **Live ChromaDB Chunks:** `{rag.count()}`")
            st.markdown(f"- **Tracked Documents:** `{stats['total_documents']}` ({stats['indexed_documents']} indexed)")
