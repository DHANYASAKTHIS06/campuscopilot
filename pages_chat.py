"""AcadFlow — Ask AcadFlow (AI Chat Interface)"""
import streamlit as st
import agents
import db
import ui


def show(user: dict):
    ui.render_chrome(
        user,
        "Ask AcadFlow",
        "Conversational AI with hybrid RAG citations from uploaded institutional documents.",
        breadcrumbs=["Student Home", "AI Assistant", "Conversation"],
    )

    uid = user["id"]

    with st.sidebar:
        st.markdown("---")
        st.markdown("**🎓 Student Profile (Eligibility)**")
        parts = []
        if user.get("department"):
            parts.append(f"Dept: {user['department']}")
        if user.get("semester"):
            parts.append(f"Sem: {user['semester']}")
        if user.get("cgpa"):
            parts.append(f"CGPA: {user['cgpa']}")
        if user.get("family_income"):
            parts.append(f"Income: ₹{user['family_income']}")
        profile = st.text_area(
            "Profile context",
            value=", ".join(parts),
            placeholder="Dept: CSE, Sem 5, CGPA 8.2, Income: 300000",
            height=85,
        )
        language_hint = st.selectbox(
            "Response Language",
            ["Auto-detect", "English", "Tamil", "Hindi", "Telugu"],
        )
        if st.button("🗑 Clear Chat History", use_container_width=True):
            st.session_state["chat_messages"] = []
            db.delete_chat_history(uid)
            st.toast("Chat history cleared.", icon="🗑")
            st.rerun()

    if "chat_messages" not in st.session_state:
        history = db.get_chat_history(uid, limit=20)
        st.session_state["chat_messages"] = []
        for h in history:
            st.session_state["chat_messages"].append({"role": "user", "content": h["question"]})
            st.session_state["chat_messages"].append({
                "role": "ai",
                "content": h["answer"],
                "chunks": h.get("sources", []),
                "verification": None,
                "eligibility": None,
                "plan": None,
            })

    messages = st.session_state["chat_messages"]

    if not messages:
        st.markdown(
            '<div class="card" style="text-align:center;padding:2.5rem 1.5rem">'
            '<div style="font-size:2.5rem;margin-bottom:.75rem">✨</div>'
            '<h3 style="margin:0 0 .35rem;color:#0F172A">Welcome to AcadFlow Assistant</h3>'
            '<p style="color:#475569;font-size:.9rem;max-width:540px;margin:0 auto 1.25rem">'
            'Say hello for normal conversation, or ask about scholarships, exams, fees, '
            'hostel rules, and procedures to search institutional PDFs.</p></div>',
            unsafe_allow_html=True,
        )
        s1, s2, s3 = st.columns(3)
        for idx, sq in enumerate([
            "Hello! What can you help me with?",
            "What is the minimum CGPA for scholarship?",
            "How do I apply for a bonafide certificate?",
        ]):
            with [s1, s2, s3][idx]:
                if st.button(sq, key=f"chat_sug_{idx}", use_container_width=True):
                    st.session_state["prefill_question"] = sq
                    st.rerun()
    else:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in messages:
            if msg["role"] == "user":
                ui.render_chat_message("user", msg["content"])
            else:
                ui.render_chat_message("ai", msg["content"])
                if msg.get("eligibility"):
                    with st.expander("🎯 Eligibility Analysis"):
                        ui.render_eligibility(msg["eligibility"])
                if msg.get("plan") and msg["plan"].get("steps"):
                    with st.expander("📋 Application Checklist"):
                        ui.render_plan(msg["plan"], user_id=uid)
                if msg.get("chunks"):
                    ui.render_sources(msg["chunks"])
                if msg.get("verification"):
                    ui.render_verification(msg["verification"])
        st.markdown("</div>", unsafe_allow_html=True)

        # Retry button if last AI response was an error
        if len(messages) >= 2 and messages[-1]["role"] == "ai" and messages[-1]["content"].startswith("[AI Error:"):
            if st.button("🔄 Retry Last Question", type="secondary"):
                last_q = messages[-2]["content"]
                st.session_state["chat_messages"] = messages[:-2]
                st.session_state["prefill_question"] = last_q
                st.rerun()

    prefill = st.session_state.pop("prefill_question", "")
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        q = st.text_input(
            "Message AcadFlow",
            value=prefill,
            placeholder="Ask a question or say Hello...",
            label_visibility="collapsed",
        )
        col_send, col_new = st.columns([3, 1])
        with col_send:
            submitted = st.form_submit_button("Send ✨", type="primary", use_container_width=True)
        with col_new:
            new_chat = st.form_submit_button("New Chat 🔄", use_container_width=True)

    if new_chat:
        st.session_state["chat_messages"] = []
        st.rerun()

    if submitted and q.strip():
        if not agents.has_api_key():
            st.error("⚠️ GEMINI_API_KEY is not configured. Please contact your administrator.")
            st.stop()

        query = q.strip()
        prior_history = list(messages)
        messages.append({"role": "user", "content": query})

        lang_map = {
            "Tamil": "tamil",
            "Hindi": "hindi",
            "Telugu": "telugu",
            "English": "english",
            "Auto-detect": None,
        }
        lang_override = lang_map.get(language_hint)

        with st.spinner("✨ AcadFlow is thinking..."):
            try:
                result = agents.run(
                    query,
                    profile=profile,
                    user_id=uid,
                    chat_history=prior_history,
                    language_override=lang_override,
                )
                answer = result["answer"]
            except Exception:
                result = {
                    "answer": "[AI Error: Unable to process request right now. Please retry.]",
                    "chunks": [],
                    "verification": None,
                    "eligibility": None,
                    "plan": None,
                    "language": "english",
                }
                answer = result["answer"]

        if not answer.startswith("[AI Error:"):
            db.save_chat(
                uid,
                query,
                answer,
                sources=result.get("chunks", []),
                language=result.get("language", "english"),
            )

        messages.append({
            "role": "ai",
            "content": answer,
            "chunks": result.get("chunks", []),
            "verification": result.get("verification"),
            "eligibility": result.get("eligibility"),
            "plan": result.get("plan"),
        })
        st.session_state["chat_messages"] = messages
        st.rerun()

    ui.render_footer()
