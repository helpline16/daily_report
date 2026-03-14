"""
Authentication module for Streamlit app
Provides simple login functionality for deployed app
"""

import streamlit as st
import hashlib


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


# Default credentials (change these!)
DEFAULT_USERS = {
    "admin": hash_password("admin123"),
    "helpline16": hash_password("helpline@2024")
}


def check_password():
    """Returns True if the user has entered correct password"""
    
    # Check if already logged in
    if st.session_state.get("authenticated", False):
        return True
    
    # Show login form
    st.markdown("### 🔐 Login Required")
    st.markdown("Please enter your credentials to access the application.")
    
    with st.form("login_form"):
        username = st.text_input("Username", key="username_input")
        password = st.text_input("Password", type="password", key="password_input")
        submit = st.form_submit_button("Login")
        
        if submit:
            # Check credentials
            if username in DEFAULT_USERS:
                if DEFAULT_USERS[username] == hash_password(password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password")
            else:
                st.error("❌ Username not found")
    
    st.markdown("---")
    st.markdown("*Contact administrator if you need access*")
    
    return False


def logout():
    """Logout the current user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()


def show_logout_button():
    """Display logout button in sidebar"""
    if st.session_state.get("authenticated", False):
        with st.sidebar:
            st.markdown("---")
            username = st.session_state.get("username", "User")
            st.markdown(f"👤 Logged in as: **{username}**")
            if st.button("🚪 Logout", use_container_width=True):
                logout()
