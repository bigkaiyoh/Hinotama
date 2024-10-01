import streamlit as st
from PIL import Image
from modules.menu import menu
from modules.modules import run_assistant, convert_image_to_text, extract_score_from_feedback
from modules.vocabvan import vocabvan_interface
from firebase_setup import db
from extra_pages.organization_dashboard import show_org_dashboard, full_org_dashboard
from extra_pages.auth_page import show_auth_page  # Import auth functions
from datetime import datetime
import uuid 


# Define the assistant ID for the main part of the app
HINOTAMA_ID = st.secrets.hinotama_id

# Session state initialization for user and organization
if 'user' not in st.session_state:
    st.session_state.user = None
if 'organization' not in st.session_state:
    st.session_state.organization = None
if 'txt' not in st.session_state:
    st.session_state.txt = ""
if 'transcription_done' not in st.session_state:
    st.session_state.transcription_done = False
if 'feedback' not in st.session_state:
    st.session_state.feedback = None

# Helper function to collect user input
def get_input():
    st.subheader("作文（さくぶん）")
    st.session_state.txt = st.text_area("こちらに文章を入力してください", height=220, value=st.session_state.txt)
    st.info(f'現在の文字数: {len(st.session_state.txt)} 文字')

    uploaded_file = st.file_uploader(
        "ファイルをアップロードしてください",
        type=["pdf", "jpg", "jpeg", "png"],
        help="手書きの文章やPDFファイルを評価するためにご利用ください"
    )
    
    if uploaded_file is not None and not st.session_state.transcription_done:
        # Transcribe the uploaded file
        with st.spinner("読み込み中..."):
            try:
                result = convert_image_to_text(uploaded_file)
                st.session_state.txt = result  # Update session state
                st.session_state.transcription_done = True
                st.success("読み込みが完了しました!")
                st.rerun()
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")

# Display AI feedback
def display_feedback():
    if 'feedback' in st.session_state and st.session_state.feedback:
        st.subheader("AIからのフィードバック")
        st.success("評価が完了しました！")

        # Display feedback in a styled box with background color
        st.markdown(f"""
            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #e8f4f8;">
                {st.session_state.feedback}
            </div>
        """, unsafe_allow_html=True)

# Save the submission to Firestore
def save_submission():
    try:
        # Reference to the submissions collection
        submissions_ref = db.collection('submissions')

        # Generate a unique submission ID
        submission_id = str(uuid.uuid4())

        # Extract score from feedback (placeholder for now)
        score = extract_score_from_feedback(st.session_state.feedback)

        # Add a new submission to the collection
        submissions_ref.document(submission_id).set({
            'submission_id': submission_id,            # Unique ID for the submission
            'user_id': st.session_state.user['id'],    # User ID of the person submitting
            'submission_text': st.session_state.txt,   # Text of the submission
            'submitAt': datetime.now(),                # Timestamp of submission
            'feedback_text': st.session_state.feedback,  # AI feedback text
            'score': score                             # Extracted score (currently None)
        })

        return True, submission_id  # Return the generated submission ID for later use

    except Exception as e:
        return False, f"Error saving submission: {e}"

# Main app function to display content
def main():
    if st.session_state.user is None and st.session_state.organization is None:
        # Call the user and organization login functions from auth_page.py
        show_auth_page() 
    else:
        # Check if an organization is logged in
        if st.session_state.organization:
            org = st.session_state.organization
            if org.get('full_dashboard', False):
                full_org_dashboard(org)  # Show full organization dashboard
            else:
                show_org_dashboard(org)  # Show limited organization dashboard
        
        # Check if a user is logged in
        elif st.session_state.user:
            user = st.session_state.user
            # Display Title with Favicon and Catchphrase using Streamlit's layout
            st.markdown("""
                <h1 class='main-title'>HINOTAMA</h1>
                <p class='catchphrase'>~その一球に魂を込めて⚾️~</p>
            """, unsafe_allow_html=True)

            menu()  # Display the app's navigation menu

            # Instructions on how to use the app
            with st.expander("📌使い方", expanded=True):
                st.markdown("""
                1. 作文を入力欄に貼り付けるか直接入力してください。  
                (ファイルをアップロードで手書き文章やPDFの添削も行えます)  
                2. 「採点する」ボタンをクリックして、AIによる評価を受けてください。
                """)

            # Chatbot Button and Popover
            with st.popover("🧠 AIに質問"):
                vocabvan_interface()

            # Get user input
            get_input()
            information = f"Writing: {st.session_state.txt}"
            
            # 提出ボタン
            submit_button = st.button("採点する🚀", type="primary")

            # Handle the evaluation and feedback display
            if submit_button:
                if user.get('status') == 'Active':
                    # Reset transcription_done and feedback states
                    st.session_state.transcription_done = False  
                    st.session_state.feedback = None

                    with st.expander("入力内容", expanded=False):
                        st.write("**提出した作文**:")
                        
                        # Use markdown to display the text in a styled box
                        box_content = st.session_state.txt.replace('\n', '<br>')
                        st.markdown(f"""
                            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f9f9f9;">
                                {box_content}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.write(f'文字数: {len(st.session_state.txt)} 文字')

                    # Run the AI assistant and get feedback
                    st.session_state.feedback = run_assistant(
                        assistant_id=HINOTAMA_ID,  # Use Hinotama assistant ID for evaluation
                        txt=information,
                        return_content=True,
                        display_chat=False
                    )
                    # Save submission
                    save_submission()

                else:
                    st.error("Your account is inactive. You cannot submit evaluations.")

            # Display AI feedback
            display_feedback()

if __name__ == "__main__":
    # Page configuration for the main app
    # fc = Image.open("src/hinotama_fv.png")
    # st.set_page_config(
    #     page_title="Hinotama",
    #     page_icon=fc,
    #     layout="wide"
    # )
    main()
