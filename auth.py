import streamlit as st
from firebase_admin import firestore
import bcrypt
from firebase_setup import db
from datetime import datetime
import pytz

def register_user(user_id, email, password, reason_for_studying, org_code, user_timezone):
    try:
        # Check if user ID already exists
        user_ref = db.collection('users').document(user_id).get()
        if user_ref.exists:  # Correct method call
            return None, "User with this ID already exists"

        # Hash the password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

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
            'status': 'Active'
        })

        # Calculate days left
        days_left = 30

        user_data = {
            "email": email,
            "id": user_id,
            "reason_for_studying": reason_for_studying,
            "org_code": org_code,
            "status": 'Active',
            "registerAt": register_at,
            'timezone': user_timezone,
            "days_left": days_left  # Active period of 30 days
        }

        return user_data, "Registration successful"
    except Exception as e:
        return None, f"Registration failed: {str(e)}"

def login_user(user_id, password):
    try:
        # Fetch user data from Firestore
        user_ref = db.collection('users').document(user_id).get()
        if not user_ref.exists:  # Correct method call
            return None, "Invalid ID or password"

        user_data = user_ref.to_dict()
        
        # Check if the provided password matches the stored hashed password
        if bcrypt.checkpw(password.encode(), user_data['password'].encode()):
            register_at = user_data.get('registerAt')
            if register_at is None:
                return None, "Registration date missing"
            
            # Update the user status based on the time passed since registration
            register_at = register_at.replace(tzinfo=pytz.utc)
            status, days_left = check_user_status(register_at)

            if status != user_data['status']:
                db.collection('users').document(user_id).update({'status': status})

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
    """Calculate whether the user is still active (within 30 days) or inactive."""
    now = datetime.now(pytz.utc)
    days_passed = (now - register_at).days
    if days_passed <= 30:
        return 'Active', 30 - days_passed
    else:
        return 'Inactive', 0

def logout_user():
    if 'user' in st.session_state:
        del st.session_state['user']
    return "Logout successful"

def login_organization(org_code, password):
    try:
        org_ref = db.collection('organizations').document(org_code).get()
        if not org_ref.exists:  # Correct method call
            return None, "Invalid organization code or password"

        org_data = org_ref.to_dict()
        if org_data['password'] == password:  # Direct comparison as password is stored in plain text
            return {
                "org_code": org_code,
                "org_name": org_data['org_name'],
                'timezone': org_data['timezone'],
                'full_dashboard': org_data.get('full_dashboard', False)
            }, "Organization login successful"
        else:
            return None, "Invalid organization code or password"
    except Exception as e:
        return None, f"Organization login failed: {str(e)}"

def logout_org():
    """Logout the organization and clear the organization session state."""
    if 'organization' in st.session_state:
        del st.session_state['organization']
    return "Organization logout successful"
