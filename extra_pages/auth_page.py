import streamlit as st
import pytz
from auth import login_user, register_user, login_organization

# Session state management for authentication steps
if 'user' not in st.session_state:
    st.session_state.user = None
if 'organization' not in st.session_state:
    st.session_state.organization = None

def show_auth_page():
    st.title("ようこそ! Welcome to Hinotama⚾️!")
    
    # Description box for Hinotama
    st.markdown("""
        <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; border: 1px solid #ddd;">
            <h3>🔥 Hinotamaとは？</h3>
            <p>Hinotamaは、AIを活用した日本語作文の添削ツールです。  
            作文を提出して、AIからフィードバックを受けましょう。  
            日本語のスキルをどんどん向上させていきましょう！</p>
        </div>
    """, unsafe_allow_html=True)

    st.header("ログイン")
    
    # Center the content
    _, col, _ = st.columns([1, 2, 1])
    
    with col:
        # Use tabs to separate user and organization authentication
        user_tab, org_tab = st.tabs(["ユーザー (User)", "教育機関 (Organization)"])
        
        with user_tab:
            show_user_auth()
        
        with org_tab:
            show_org_auth()

    # Add some space and a footer
    st.markdown("---")
    st.markdown("ご質問がある場合はお問い合わせください。 (If you have any questions, please contact us.)")
    st.markdown("メールアドレス： company@nuginy.com")


def show_user_auth():
    # Option Menu for Login and Register
    choice = st.radio("Choose action", ["User Login", "User Registration"], horizontal=True)
    
    if choice == "User Login":
        with st.form("login_form"):
            st.subheader("ユーザーログイン (User Login)")
            user_id = st.text_input("ユーザーID (User ID)")
            user_password = st.text_input("パスワード (Password)", type="password")
            login_submit = st.form_submit_button("ログイン (Login)")
            
            if login_submit:
                if user_id and user_password:
                    user_data, message = login_user(user_id, user_password)
                    if user_data:
                        st.session_state.user = user_data
                        st.success(message)
                        st.rerun()  # Rerun to load the main app
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both User ID and Password.")
    
    elif choice == "User Registration":
        with st.form("register_form"):
            st.subheader("ユーザー登録 (User Registration)")
            user_id = st.text_input("ユーザーID (User ID)")
            email = st.text_input("メールアドレス (Email)")
            password = st.text_input("パスワード (Password)", type="password")
            confirm_password = st.text_input("パスワード確認 (Confirm Password)", type="password")
            reason_for_studying = st.text_area("日本語を学ぶ理由 (Reason for Studying Japanese)")
            org_code = st.text_input("教育機関コード (Organization Code) - Optional")
            
            # Timezone selection
            timezones = pytz.all_timezones
            selected_timezone = st.selectbox("タイムゾーンを選択してください (Select Your Timezone)", timezones)
            
            register_submit = st.form_submit_button("登録 (Register)")
            
            if register_submit:
                if password != confirm_password:
                    st.error("パスワードが一致しません (Passwords do not match).")
                else:
                    user_data, message = register_user(user_id, email, password, reason_for_studying, org_code, selected_timezone)
                    if user_data:
                        st.success(message)
                        st.session_state.user = user_data
                        st.rerun()  # Rerun to load the main app
                    else:
                        st.error(message)

def show_org_auth():
    st.subheader("教育機関ログイン (Organization Login)")
    with st.form("organization_login_form"):
        org_code = st.text_input("教育機関コード (Organization Code)")
        org_password = st.text_input("パスワード (Password)", type="password")
        org_submit = st.form_submit_button("ログイン (Organization Login)")
        
        if org_submit and org_code and org_password:
            org_data, message = login_organization(org_code, org_password)
            if org_data:
                st.session_state.organization = org_data
                st.success(message)
                st.rerun()  # Rerun to load the org dashboard
            elif org_code == "MKT":
                st.switch_page("pages/marketing_dashboard.py")
            else:
                st.error(message)