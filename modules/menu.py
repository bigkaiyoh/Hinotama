import streamlit as st
from auth import logout_user

# Initialize session states if not set
if 'user' not in st.session_state:
    st.session_state.user = None

def authenticated_menu():
    user = st.session_state.user
    # Show a navigation menu for authenticated users
    with st.sidebar:
        st.image("https://nuginy.com/wp-content/uploads/2024/08/Hinotama-favicon_HighRes.png", width=190)
        st.sidebar.write(f"おかえりなさい、{user['id']}さん！")
        st.divider()

        # Provide page links relevant to Hinotama
        st.page_link("app.py", label="ホーム", icon="🏠")
        st.page_link("pages/Settings.py", label="設定", icon="⚙️")
        
        if st.button("ログアウト"):
            logout_user()
            st.rerun()

def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    with st.sidebar:
        st.image("https://nuginy.com/wp-content/uploads/2024/08/Hinotama-favicon_HighRes.png", width=190)
        if st.button("ログイン"):
            st.switch_page("auth_page.py")

def menu():
    # Determine if a user is logged in or not, then show the appropriate navigation menu
    if st.session_state.user is None:
        unauthenticated_menu()
    else:
        authenticated_menu()

    # Custom CSS with updated hover color
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #0097B2;
        color: white;
        padding: 10px 24px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #007A8F;
    }
    </style>
    """, unsafe_allow_html=True)
