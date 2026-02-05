"""
Login and Signup pages for the dashboard.
"""
import streamlit as st
import re
from dashboard.auth_utils import login_user, signup_user

def render_login_page():
    """Render the login/signup UI."""
    
    st.markdown("""
    <style>
        .auth-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #f0f2f6;
            border-radius: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🎬 MovieMind</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Your Personal Movie Recommender</h3>", unsafe_allow_html=True)
        st.write("")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log In", width="stretch")
                
                if submitted:
                    if not email or not password:
                        st.error("Please enter email and password")
                    else:
                        with st.spinner("Logging in..."):
                            success, msg = login_user(email, password)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
        
        with tab2:
            with st.form("signup_form"):
                new_email = st.text_input("Email")
                new_name = st.text_input("Display Name")
                new_password = st.text_input("Password", type="password", help="Min 8 chars, 1 uppercase, 1 lowercase, 1 number")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                submitted = st.form_submit_button("Create Account", width="stretch")
                
                if submitted:
                    if not new_email or not new_name or not new_password:
                        st.error("All fields are required")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password too short")
                    else:
                        with st.spinner("Creating account..."):
                            success, msg = signup_user(new_email, new_password, new_name)
                            if success:
                                st.success(msg)
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(msg)
                                
        st.divider()
        st.info("💡 **Demo Accounts:**\n\n- `demo@example.com` / `DemoPass123`\n- Or create a new account to see cold start recommendations!")
