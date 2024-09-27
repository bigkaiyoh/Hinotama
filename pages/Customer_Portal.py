import streamlit as st
import stripe
from modules.menu import menu
from modules.modules import get_stripe_secret, run_stripe, translate

# Removing Streamlit Header and Footer for a cleaner look
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Set up Stripe API
stripe.api_key = get_stripe_secret("firestore-stripe-payments-STRIPE_API_KEY")

# Initialize Session_State
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'JP' not in st.session_state:
    st.session_state.JP = False


def main():
    menu()

    # Check if user is logged in
    if st.session_state.user:
        st.sidebar.write("Successfully Logged in!")
        st.sidebar.write(st.session_state.user['nickname'])

        st.title(translate('カスタマーポータル', 'Customer Portal'))

        # Retrieve the customer ID from session state
        customer_id = st.session_state.user.get('customer_id')

        if customer_id:
            run_stripe(customer_id)
        else:
            st.error(translate("顧客IDが見つかりません。サポートにお問い合わせください。",
                               "Customer ID not found. Please contact support."))
    else:
        st.warning(translate("ログインが必要です。", "You need to be logged in to access this page."))
        st.stop()

    # Explain Customer Portal
    st.write(translate("""\n
        
        #### できること
        **プランの管理:**
        - サブスクリプションプランを表示および変更します。
        - サブスクリプションをアップグレード、ダウングレード、またはキャンセルします。

        **アカウント情報の変更:**
        - 名前、メールアドレス、および支払い方法の更新。\n
        """,
        """\n
        
        #### Instructions
        **Manage Your Plan:**
        - View and modify your subscription plan.
        - Upgrade, downgrade, or cancel your subscription.

        **Modify Your Account Information:**
        - Update your name, email, and the method of payment.\n
        """))
    
    st.divider()

if __name__ == "__main__":
    # st.set_page_config(page_title="Customer Portal", page_icon="👤", layout="wide")
    main()
