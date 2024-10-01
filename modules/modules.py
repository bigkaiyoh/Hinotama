import streamlit as st
from openai import OpenAI
import time
from PIL import Image
import base64
import requests
import json
import re

# Fetch OpenAI API key from Streamlit secrets
api = st.secrets.api_key

# Initialize OpenAI client only once
client = OpenAI(api_key=api)

def extract_score_from_feedback(feedback_text):
    """
    Extract the score from AI-generated feedback text.
    The function uses regex to find the score after the keyword スコア (Score).
    """
    # Regular expression to find "スコア:" followed by a number (possibly ending with "点")
    match = re.search(r"スコア:?\s*\*?\*?\s*(\d+(\.\d+)?)", feedback_text)
    
    if match:
        return float(match.group(1))
    
    # If no match found, return None
    return None

def run_assistant(assistant_id, txt, return_content=False, display_chat=True):
    # Check if client is already in session state
    if 'client' not in st.session_state:
        st.session_state.client = client  # Use globally initialized client

    # Retrieve the assistant
    st.session_state.assistant = st.session_state.client.beta.assistants.retrieve(assistant_id)

    # Create a thread
    st.session_state.thread = st.session_state.client.beta.threads.create()
    content = ""

    if txt:
        # Add a message to the thread
        st.session_state.client.beta.threads.messages.create(
            thread_id=st.session_state.thread.id,
            role="user",
            content=txt
        )

        # Run the Assistant
        run = st.session_state.client.beta.threads.runs.create(
            thread_id=st.session_state.thread.id,
            assistant_id=st.session_state.assistant.id
        )

        # Spinner for ongoing process
        with st.spinner('One moment...'):
            while True:
                # Retrieve the run status
                run_status = st.session_state.client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread.id,
                    run_id=run.id
                )

                # If run is completed, process messages
                if run_status.status == 'completed':
                    messages = st.session_state.client.beta.threads.messages.list(
                        thread_id=st.session_state.thread.id
                    )

                    # Loop through messages and display based on role
                    for msg in reversed(messages.data):
                        role = msg.role
                        content = msg.content[0].text.value
                        
                        if display_chat:
                            with st.chat_message(role):
                                st.write(content)
                    break

                # Wait before checking status again
                time.sleep(1)

    if return_content:
        return content

# ------------------ transcribe with GPT-4 vision -------------------------
def convert_image_to_text(uploaded_file):
    # Function to encode the image
    def encode_image(image_file):
        return base64.b64encode(image_file.read()).decode('utf-8')

    # Encode the uploaded file
    base64_image = encode_image(uploaded_file)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api}"
    }

    # Modify the payload based on the specific API requirements
    payload = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please transcribe the handwritten text in this image."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error in API call: {response.status_code} - {response.text}")
