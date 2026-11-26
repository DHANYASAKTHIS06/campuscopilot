"""AcadFlow — Landing & Authentication Page"""
import streamlit as st
import db
import ui


def show():
    ui.inject_css()

    left_col, right_col = st.columns([1.1, 1], gap="large")

    with left_col:
        st.markdown(
            f'<div style="padding:1rem .25rem .5rem">'
            f'<div style="display:flex;align-items:center;gap:.9rem;margin-bottom:1.25rem">'
            f'<div style="width:54px;height:54px;border-radius:14px;'
            f'background:linear-gradient(135deg,#3867F4 0%,#7656E8 62%,#06B6D4 100%);'
            f'display:flex;align-items:center;justify-content:center;'
            f'box-shadow:0 8px 22px rgba(56,103,244,.28)">{ui.LOGO_SVG}</div>'
            f'<div><h1 style="font-size:2.1rem;font-weight:800;margin:0;color:#172554;'
            f'letter-spacing:-.03em">{ui.BRAND_NAME}</h1>'
            f'<p style="margin:0;font-size:.9rem;font-weight:700;color:#7656E8">'
            f'{ui.BRAND_TAGLINE}</p></div></div>'
            f'<p style="font-size:.98rem;color:#667085;line-height:1.65;margin-bottom:1.4rem">'
            f'{ui.BRAND_DESC}</p>'
            f'<div class="feature-card">'
            f'<strong style="color:#3867F4">✨ Document-Grounded AI Assistant</strong>'
            f'<div style="font-size:.84rem;color:#667085;margin-top:.25rem">'
            f'Hybrid BM25 + Vector RAG powered by Google Gemini with verified page citations.</div></div>'
            f'<div class="feature-card violet">'
            f'<strong style="color:#7656E8">🎯 Smart Eligibility & Planning</strong>'
            f'<div style="font-size:.84rem;color:#667085;margin-top:.25rem">'
            f'Evaluate scholarship criteria, build step-by-step checklists, and export deadlines.</div></div>'
            f'<div class="feature-card cyan">'
            f'<strong style="color:#0891B2">📝 Application Studio & Helpdesk</strong>'
            f'<div style="font-size:.84rem;color:#667085;margin-top:.25rem">'
            f'Draft formal institutional letters as A4 PDFs and track support tickets.</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        with st.container(border=True):
            st.markdown(
                '<div style="margin-bottom:.35rem">'
                '<h2 style="font-size:1.25rem;font-weight:800;color:#172554;margin:0">Access AcadFlow</h2>'
                '<p style="font-size:.84rem;color:#667085;margin:.2rem 0 .6rem">'
                'Sign in to your institutional account or register as a student.</p></div>',
                unsafe_allow_html=True,
            )

            tab_login, tab_reg = st.tabs(["🔑 Sign In", "🆕 Create Student Account"])

            with tab_login:
                with st.form("login_form", border=False):
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
                    '<div style="text-align:center;margin-top:.5rem;font-size:.78rem;color:#667085">'
                    'Supported Roles: Student · Administrator · Helpdesk Officer</div>',
                    unsafe_allow_html=True,
                )

            with tab_reg:
                with st.form("reg_form", border=False):
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

    ui.render_footer()
