import streamlit as st
from modules.modules import run_assistant

def vocabvan_interface():
    assistant = st.secrets.vocabvan_JP

    user_input = st.chat_input("質問を入力してください。言いたいことや状況を含めて、自然な日本語表現を提案します。")

    temporary = st.empty()
    t = temporary.container()

    with t:
        st.write("の作文練習をサポートするために、正確で自然な日本語表現を提案します。")
        m1 = st.chat_message("user")
        a1 = st.chat_message("assistant")
        m2 = st.chat_message("user")
        a2 = st.chat_message("assistant")
        m3 = st.chat_message("user")
        a3 = st.chat_message("assistant")

        # Scenario 1: User wants to know how to express gratitude in a formal manner
        m1.write("先生に感謝の気持ちを伝える作文を書きたいです。どんな表現が良いですか？")
        a1.write("""1. "先生、いつも丁寧にご指導いただき、心より感謝申し上げます。" – 丁寧でフォーマルな感謝の表現。
2. "おかげさまで、たくさんのことを学びました。深く感謝しております。" – 感謝の気持ちを強調するフォーマルな表現。
3. "ご指導ありがとうございました。今後ともよろしくお願い申し上げます。" – 丁寧で締めの言葉としても使える表現。""")

        # Scenario 2: User asks how to describe a daily routine
        m2.write("毎朝学校に行く")
        a2.write("""1. "毎朝学校に通っています。" – より一般的な表現。
2. "毎朝学校に向かいます。" – "向かう" を使った表現。
3. "毎朝、学校へ行く準備をしています。" – 行動の一部を強調した表現。""")

        # Scenario 3: User asks how to improve a sentence they've written
        m3.write("「昨日はとてもいい天気だった。」という文をもっと自然に直してください。")
        a3.write("""1. "昨日は本当にいい天気でした。" – より自然な表現。
2. "昨日は快晴で、とても過ごしやすい一日でした。" – 少し詳しく状況を説明した表現。
3. "昨日の天気は素晴らしく、気持ちの良い日でした。" – 感情を強調した表現。""")

    if user_input:
        # Clear client, assistant, and thread from session state to ensure a new thread is created
        if 'client' in st.session_state:
            del st.session_state.client
        if 'assistant' in st.session_state:
            del st.session_state.assistant
        if 'thread' in st.session_state:
            del st.session_state.thread
        temporary.empty()
        run_assistant(assistant_id=assistant, txt=user_input)

    return user_input