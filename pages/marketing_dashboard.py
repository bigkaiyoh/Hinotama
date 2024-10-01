import streamlit as st
import pandas as pd
import plotly.express as px
from firebase_setup import db
from datetime import datetime, timedelta
import pytz
from google.cloud.firestore import Query

# Streamlit page config
st.set_page_config(page_title="Hinotama Marketing Dashboard", layout="wide")

# Cache Firestore queries
@st.cache_data(ttl=600)
def query_firestore(limit=1000):
    users_ref = db.collection('users')
    submissions_ref = db.collection('submissions')
    login_events_ref = db.collection('login_events')

    users = list(users_ref.limit(limit).stream())
    submissions = list(submissions_ref.limit(limit).stream())
    login_events = list(login_events_ref.limit(limit).stream())

    # Convert document snapshots to a combination of dict and id for ease of use
    users_data = [{"id": user.id, **user.to_dict()} for user in users]
    submissions_data = [doc.to_dict() for doc in submissions]
    login_events_data = [doc.to_dict() for doc in login_events]

    return users_data, submissions_data, login_events_data

@st.cache_data(ttl=600)
def query_filtered_firestore(start_date, end_date, limit=1000):
    submissions_ref = db.collection('submissions')
    login_events_ref = db.collection('login_events')

    submissions = list(submissions_ref.where('submitAt', '>=', start_date).where('submitAt', '<=', end_date).limit(limit).stream())
    login_events = list(login_events_ref.where('timestamp', '>=', start_date).where('timestamp', '<=', end_date).limit(limit).stream())

    # Convert document snapshots to dict for ease of use
    submissions_data = [doc.to_dict() for doc in submissions]
    login_events_data = [doc.to_dict() for doc in login_events]

    return submissions_data, login_events_data

# Helper functions
def get_active_user_count(users):
    return sum(1 for user in users if user.get('status') == 'Active')

def get_total_user_count(users):
    return len(users)

def calculate_multiple_submission_rate(submissions):
    today = datetime.now(pytz.utc).date()
    users_with_submissions = set()
    users_with_multiple_submissions = set()

    for submission in submissions:
        submit_time = submission.get('submitAt').date()
        user_id = submission.get('user_id')

        if submit_time == today:
            if user_id in users_with_submissions:
                users_with_multiple_submissions.add(user_id)
            else:
                users_with_submissions.add(user_id)

    if len(users_with_submissions) == 0:
        return 0

    return (len(users_with_multiple_submissions) / len(users_with_submissions)) * 100

def calculate_retention_rate(users, login_events):
    today = datetime.now(pytz.utc)
    eligible_users = [user for user in users if user.get('registerAt') <= (today - timedelta(days=14))]

    retained_users_count = 0
    for user in eligible_users:
        user_id = user.get('id')
        recent_logins = [event for event in login_events if event.get('user_id') == user_id and event.get('timestamp') >= (today - timedelta(weeks=2))]
        if len(recent_logins) >= 2:
            retained_users_count += 1

    if len(eligible_users) == 0:
        return 0

    return (retained_users_count / len(eligible_users)) * 100

def calculate_average_submissions(submissions, active_user_count):
    if active_user_count == 0:
        return 0
    return len(submissions) / active_user_count

def calculate_score_improvement(submissions):
    user_scores = {}
    for submission in submissions:
        user_id = submission.get('user_id')
        score = submission.get('score')
        if score is not None:
            if user_id not in user_scores:
                user_scores[user_id] = []
            user_scores[user_id].append(score)

    user_improvements = []
    for scores in user_scores.values():
        if len(scores) > 1:
            user_improvements.append(scores[-1] - scores[0])

    if len(user_improvements) == 0:
        return 0

    return sum(user_improvements) / len(user_improvements)

# Main function
def main():
    st.title("Hinotama Marketing Dashboard")

    # Load data for Signpost Metrics (without date filters)
    with st.spinner("Loading data for Signpost Metrics..."):
        users, submissions, login_events = query_firestore()

    # Tabs for different sections of the dashboard
    tab1, tab2, tab3 = st.tabs(["サインポスト指標 (Signpost Metrics)", "ノーススターメトリック (North Star Metrics)", "個々のユーザー詳細 (Individual User Details)"])

    # -- サインポスト指標 (Signpost Metrics) --
    with tab1:
        st.header("サインポスト指標 (Signpost Metrics)")
        active_user_count = get_active_user_count(users)
        total_user_count = get_total_user_count(users)
        daily_multiple_submission_rate = calculate_multiple_submission_rate(submissions)
        retention_rate = calculate_retention_rate(users, login_events)

        # Display metrics in columns for Signpost Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("総テストユーザー数 (Total Active Users)", active_user_count)
        col2.metric("累計ユーザー数 (Total Users)", total_user_count)
        col3.metric("1日内の複数回提出率 (Daily Multiple Submission Rate)", f"{daily_multiple_submission_rate:.2f}%")
        col4.metric("継続利用率 (Retention Rate)", f"{retention_rate:.2f}%")

    # -- ノーススターメトリック (North Star Metrics) --
    with tab2:
        st.header("ノーススターメトリック (North Star Metrics)")

        # Date range selector for North Star Metrics
        col1, col2 = st.columns(2)
        start_date = col1.date_input("Start Date", datetime.now(pytz.utc) - timedelta(days=30))
        end_date = col2.date_input("End Date", datetime.now(pytz.utc))

        if start_date <= end_date:
            start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=pytz.utc)
            end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=pytz.utc)

            with st.spinner("Loading data for North Star Metrics..."):
                filtered_submissions, filtered_login_events = query_filtered_firestore(start_datetime, end_datetime)

            average_submissions_per_user = calculate_average_submissions(filtered_submissions, active_user_count)
            score_improvement = calculate_score_improvement(filtered_submissions)

            # Display metrics for North Star Metrics
            st.metric("平均提出数 (Average Submissions per User)", f"{average_submissions_per_user:.2f}")
            st.metric("平均スコア改善度 (Average Score Improvement)", f"{score_improvement:.2f}")

            # Score Improvement over time visualization
            st.subheader("ユーザースコア推移 (User Score Progression)")
            score_data = pd.DataFrame({
                "User ID": [sub.get('user_id') for sub in filtered_submissions],
                "Score": [sub.get('score', 0) for sub in filtered_submissions],
                "Date": [sub.get('submitAt') for sub in filtered_submissions]
            })
            if not score_data.empty:
                fig = px.line(score_data, x="Date", y="Score", color="User ID", title="User Score Progression")
                st.plotly_chart(fig, use_container_width=True)

    # -- 個々のユーザー詳細 (Individual User Details) --
    with tab3:
        st.header("個々のユーザー詳細 (Individual User Details)")
        user_ids = [user['id'] for user in users]
        selected_user = st.selectbox("ユーザーを選択してください (Select User)", options=user_ids)

        if selected_user:
            user_data = next((user for user in users if user['id'] == selected_user), None)
            if user_data:
                st.write(f"**ユーザーID**: {selected_user}")
                st.write(f"**学習目的 (Reason for Studying)**: {user_data.get('reason_for_studying', 'N/A')}")
                st.write(f"**ステータス (Status)**: {user_data.get('status', 'N/A')}")

                # Display Submission History
                user_submissions = [sub for sub in submissions if sub.get('user_id') == selected_user]
                st.subheader("提出履歴 (Submission History)")
                submission_df = pd.DataFrame(user_submissions)
                if not submission_df.empty:
                    submission_df['submitAt'] = pd.to_datetime(submission_df['submitAt'])
                    submission_df = submission_df.sort_values('submitAt', ascending=False)
                    st.dataframe(submission_df[['submitAt', 'score', 'submission_text']])
                else:
                    st.write("このユーザーの提出履歴はありません。")

                # Display Login History
                user_login_events = [event for event in login_events if event.get('user_id') == selected_user]
                st.subheader("ログイン履歴 (Login History)")
                login_df = pd.DataFrame(user_login_events)
                if not login_df.empty:
                    login_df['timestamp'] = pd.to_datetime(login_df['timestamp'])
                    login_df = login_df.sort_values('timestamp', ascending=False)
                    st.dataframe(login_df[['timestamp', 'device_type', 'browser']])
                else:
                    st.write("このユーザーのログイン履歴はありません。")

if __name__ == "__main__":
    main()
