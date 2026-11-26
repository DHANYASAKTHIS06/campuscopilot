"""AcadFlow — Landing & Authentication Page"""
import streamlit as st
import db
import ui


def show():
    ui.inject_css()

    left_col, right_col = st.columns([1.15, 1], gap="large")

    with left_col:
        st.markdown(
            f'<div style="padding:1.5rem .5rem 1rem">'
            f'<div style="display:flex;align-items:center;gap:.85rem;margin-bottom:1.25rem">'
            f'<div style="width:52px;height:52px;border-radius:14px;'
            f'background:linear-gradient(135deg,#2563EB 0%,#7C3AED 60%,#06B6D4 100%);'
            f'display:flex;align-items:center;justify-content:center;'
            f'box-shadow:0 8px 20px rgba(37,99,235,.25)">{ui.LOGO_SVG}</div>'
            f'<div><h1 style="font-size:2rem;font-weight:800;margin:0;color:#0F172A;'
            f'letter-spacing:-.03em">{ui.BRAND_NAME}</h1>'
            f'<p style="margin:0;font-size:.88rem;font-weight:600;color:#7C3AED">'
            f'{ui.BRAND_TAGLINE}</p></div></div>'
            f'<p style="font-size:.98rem;color:#475569;line-height:1.65;margin-bottom:1.5rem">'
            f'{ui.BRAND_DESC}</p>'
            f'<div class="feature-card">'
            f'<strong style="color:#2563EB">✨ Document-Grounded AI Assistant</strong>'
            f'<div style="font-size:.84rem;color:#475569;margin-top:.2rem">'
            f'Hybrid BM25 + Vector RAG with verified citations and page references.</div></div>'
            f'<div class="feature-card violet">'
            f'<strong style="color:#7C3AED">🎯 Smart Eligibility & Planning</strong>'
            f'<div style="font-size:.84rem;color:#475569;margin-top:.2rem">'
            f'Evaluate scholarship criteria, build step-by-step checklists, and export deadlines.</div></div>'
            f'<div class="feature-card cyan">'
            f'<strong style="color:#0891B2">📝 Application Studio & Helpdesk</strong>'
            f'<div style="font-size:.84rem;color:#475569;margin-top:.2rem">'
            f'Draft formal institutional letters as PDFs and track helpdesk support tickets.</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown('<div style="padding-top:1rem">', unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["🔑 Sign In", "🆕 Create Student Account"])

        with tab_login:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### Welcome back")
            st.caption("Sign in with your institutional credentials.")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

            if submitted:
                if not username.strip() or not password:
                    st.error("Please enter both username and password.")
                else:
                    user = db.authenticate(username.strip(), password)
                    if user:
                        token = db.create_session(user["id"])
                        st.session_state["auth_token"] = token
                        st.session_state["user"] = user
                        ui.navigate("dashboard")
                    else:
                        st.error("❌ Invalid username or password.")

            st.markdown(
                '<div style="text-align:center;margin-top:.6rem;font-size:.78rem;color:#64748B">'
                'Roles: Student · Administrator · Helpdesk Officer</div>',
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_reg:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### Student Registration")
            with st.form("reg_form"):
                r_name = st.text_input("Full Name *", placeholder="Your full name")
                r_user = st.text_input("Username *", placeholder="Choose a username")
                r_email = st.text_input("Institutional Email", placeholder="student@institution.edu")
                c1, c2 = st.columns(2)
                with c1:
                    r_dept = st.text_input("Department", placeholder="e.g. CSE")
                    r_cgpa = st.text_input("CGPA", placeholder="e.g. 8.5")
                with c2:
                    r_sem = st.text_input("Semester", placeholder="e.g. 5")
                    r_income = st.text_input("Family Income (₹)", placeholder="e.g. 300000")
                r_pass = st.text_input("Password *", type="password", placeholder="Min 6 characters")
                r_pass2 = st.text_input("Confirm Password *", type="password")
                reg_submit = st.form_submit_button("Create Account →", type="primary", use_container_width=True)

            if reg_submit:
                if not r_name.strip() or not r_user.strip() or not r_pass:
                    st.error("Full name, username, and password are required.")
                elif r_pass != r_pass2:
                    st.error("Passwords do not match.")
                elif len(r_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    uid = db.create_user(
                        username=r_user.strip(),
                        email=r_email.strip() or None,
                        password=r_pass,
                        role="student",
                        full_name=r_name.strip(),
                        department=r_dept.strip(),
                        semester=r_sem.strip(),
                        cgpa=r_cgpa.strip(),
                        family_income=r_income.strip(),
                    )
                    if uid:
                        st.success("✅ Student account created! Switch to Sign In to continue.")
                    else:
                        st.error("Username or email already exists. Please choose another.")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    ui.render_footer()
