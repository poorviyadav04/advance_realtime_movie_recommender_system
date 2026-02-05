"""
Authentication utilities for the Streamlit dashboard.
"""
import streamlit as st
import requests
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"

def login_user(email, password):
    """
    Authenticate user and store token in session state.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.user_info = data["user"]
            st.session_state.authenticated = True
            st.session_state.current_user_id = data["user"]["user_id"]
            return True, "Login successful"
        else:
            return False, response.json().get("detail", "Login failed")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def signup_user(email, password, display_name):
    """
    Create new user account.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/signup",
            json={
                "email": email, 
                "password": password,
                "display_name": display_name
            },
            timeout=5
        )
        
        if response.status_code == 201:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.user_info = data["user"]
            st.session_state.authenticated = True
            st.session_state.current_user_id = data["user"]["user_id"]
            return True, "Account created successfully"
        else:
            try:
                error_detail = response.json().get("detail", "Signup failed")
            except ValueError:
                error_detail = f"Server Error ({response.status_code}): {response.text[:100]}"
            return False, error_detail
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def logout_user():
    """
    Clear session state and logout.
    """
    if "token" in st.session_state:
        # Optional: Call API to invalidate session
        try:
            requests.post(
                f"{API_BASE_URL}/auth/logout",
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                timeout=3
            )
        except:
            pass
            
    # Clear session keys
    keys_to_clear = ["token", "user_info", "authenticated", "current_user_id"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    st.rerun()

def get_auth_headers():
    """Get Authorization headers for API calls."""
    if "token" in st.session_state:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}
