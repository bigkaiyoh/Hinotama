import streamlit as st
from firebase_admin import firestore
import bcrypt
from firebase_setup import db
from datetime import datetime
import pytz
import uuid
import streamlit.components.v1 as components

ACTIVE_PERIOD_DAYS = 30


def register_user(user_id, email, password, reason_for_studying, org_code, user_timezone):
    try:
        # Check if user ID already exists
        user_ref = db.collection('users').document(user_id).get()
        if user_ref.exists:
            return None, "User with this ID already exists"

        # Hash the password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Validate if org_code exists
        if org_code:
            org_ref = db.collection('organizations').document(org_code).get()
            if not org_ref.exists:
                return None, "Invalid organization code provided."

        # Use UTC timezone-aware datetime for registration timestamp
        register_at = datetime.now(pytz.utc)

        # Create a new user document in Firestore
        db.collection('users').document(user_id).set({
            'email': email,
            'password': hashed_password,
            'reason_for_studying': reason_for_studying,
            'org_code': org_code,
            'registerAt': register_at,
            'timezone': user_timezone,
            'status': 'Active'                        # User status starts as 'Active'
        })

        # Calculate days left (for the MVP active trial period)
        days_left = ACTIVE_PERIOD_DAYS

        user_data = {
            "id": user_id,
            "email": email,
            "reason_for_studying": reason_for_studying,
            "org_code": org_code,
            "status": 'Active',
            "registerAt": register_at,
            'timezone': user_timezone,
            "days_left": days_left
        }

        return user_data, "Registration successful"
    except Exception as e:
        return None, f"Registration failed: {str(e)}"

def login_user(user_id, password):
    try:
        # Fetch user data from Firestore
        user_ref = db.collection('users').document(user_id).get()
        if not user_ref.exists:
            return None, "Invalid ID or password"

        user_data = user_ref.to_dict()
        
        # Check if the provided password matches the stored hashed password
        if bcrypt.checkpw(password.encode(), user_data['password'].encode()):
            register_at = user_data.get('registerAt')

            # Handle missing registerAt field
            if register_at is None:
                # Log the missing registration date and inform the user to contact support
                log_missing_register_at(user_id)
                return None, "There seems to be an issue with your registration data. Please contact support to resolve it."

            # Update the user status based on the time passed since registration
            register_at = register_at.replace(tzinfo=pytz.utc)
            status, days_left = check_user_status(register_at)

            # Update Firestore if the user status has changed
            if status != user_data['status']:
                db.collection('users').document(user_id).update({'status': status})

            # Log the login event
            log_login_event(user_id)

            return {
                "id": user_id,
                "email": user_data['email'],
                "reason_for_studying": user_data['reason_for_studying'],
                "org_code": user_data['org_code'],
                'timezone': user_data['timezone'],
                "status": status,
                "days_left": days_left
            }, "Login successful"
        else:
            return None, "Invalid ID or password"
    except Exception as e:
        return None, f"Login failed: {str(e)}"



def check_user_status(register_at):
    """Calculate whether the user is still active (within the set days) or inactive."""
    now = datetime.now(pytz.utc)
    days_passed = (now - register_at).days
    if days_passed <= ACTIVE_PERIOD_DAYS:
        return 'Active', ACTIVE_PERIOD_DAYS - days_passed
    else:
        return 'Inactive', 0

def logout_user():
    if 'user' in st.session_state:
        del st.session_state['user']
    return "Logout successful"

def login_organization(org_code, password):
    try:
        org_ref = db.collection('organizations').document(org_code).get()
        if not org_ref.exists:
            return None, "Invalid organization code or password"

        org_data = org_ref.to_dict()
        # Direct comparison as password is stored in plain text (since orgs are added manually)
        if org_data['password'] == password:
            return {
                "org_code": org_code,
                "org_name": org_data['org_name'],
                'timezone': org_data.get('timezone', 'UTC'),
                'full_dashboard': org_data.get('full_dashboard', False)
            }, "Organization login successful"
        else:
            return None, "Invalid organization code or password"
    except Exception as e:
        return None, f"Organization login failed: {str(e)}"

def logout_org():
    if 'organization' in st.session_state:
        del st.session_state['organization']
    return "Organization logout successful"



# Function to detect browser and device type using JavaScript
def get_device_and_browser():
    # JavaScript to get browser and device type and send it back via Streamlit
    js_code = """
        <script>
            function sendBrowserInfo() {
                var userAgent = navigator.userAgent;
                var browserName = "Unknown";
                var deviceType = "Unknown";

                // Detecting browser type
                if (userAgent.indexOf("Chrome") > -1) {
                    browserName = "Chrome";
                } else if (userAgent.indexOf("Safari") > -1 && userAgent.indexOf("Chrome") === -1) {
                    browserName = "Safari";
                } else if (userAgent.indexOf("Firefox") > -1) {
                    browserName = "Firefox";
                } else if (userAgent.indexOf("Edge") > -1) {
                    browserName = "Edge";
                } else if (userAgent.indexOf("Opera") > -1 || userAgent.indexOf("OPR") > -1) {
                    browserName = "Opera";
                } else if (userAgent.indexOf("Trident") > -1) {
                    browserName = "Internet Explorer";
                }

                // Detecting device type
                if (userAgent.indexOf("Mobi") > -1) {
                    deviceType = "Mobile";
                } else {
                    deviceType = "Desktop";
                }

                // Sending information to Streamlit using a hidden input field
                const browserInfo = browserName + ";" + deviceType;
                const input = document.createElement("input");
                input.type = "hidden";
                input.id = "browser-info";
                input.value = browserInfo;
                document.body.appendChild(input);
            }
            window.onload = sendBrowserInfo;
        </script>
        <div id="browser-info" style="display: none;"></div>
    """
    
    # Inject JavaScript into the app to run on page load
    components.html(js_code, height=0)

    # Placeholder for hidden browser information
    if 'browser' not in st.session_state or 'device_type' not in st.session_state:
        st.session_state['browser'] = "Unknown"
        st.session_state['device_type'] = "Unknown"

# Function to log login events
def log_login_event(user_id):
    """Logs a login event in the Firestore login_events collection."""
    try:
        device_type = st.session_state.get("device_type", "Unknown - JS detection failed")
        browser = st.session_state.get("browser", "Unknown - JS detection failed")

        login_event_id = str(uuid.uuid4())
        db.collection('login_events').document(login_event_id).set({
            'user_id': user_id,
            'timestamp': datetime.now(pytz.utc),
            'device_type': device_type,
            'browser': browser
        })
    except Exception as e:
        st.error(f"Failed to log login event: {str(e)}")

# Function to log issues with missing registration dates
def log_missing_register_at(user_id):
    try:
        db.collection('user_issues').add({
            'user_id': user_id,
            'issue': 'Missing registerAt',
            'timestamp': datetime.now(pytz.utc)
        })
    except Exception as e:
        st.error(f"Failed to log issue for user {user_id}: {str(e)}")