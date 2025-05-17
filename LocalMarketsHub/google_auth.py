import json
import os
import requests
from app import app, db
from flask import Blueprint, redirect, request, url_for
from flask_login import login_required, login_user, logout_user, current_user
from models import User
from oauthlib.oauth2 import WebApplicationClient

# Configuration for Google OAuth
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Create Blueprint
google_auth = Blueprint("google_auth", __name__)

# Check if Google OAuth is configured
google_oauth_configured = GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET

if google_oauth_configured:
    # Initialize OAuth client
    client = WebApplicationClient(GOOGLE_CLIENT_ID)

    @google_auth.route("/google_login")
    def login():
        # Find out what URL to hit for Google login
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)

    @google_auth.route("/google_login/callback")
    def callback():
        # Get authorization code Google sent back
        code = request.args.get("code")
        
        # Find out what URL to hit to get tokens
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Prepare and send a request to get tokens
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=request.base_url.replace("http://", "https://"),
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Get user info
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        # Process user info
        userinfo = userinfo_response.json()
        
        # Verify email
        if userinfo.get("email_verified"):
            unique_id = userinfo["sub"]
            users_email = userinfo["email"]
            picture = userinfo.get("picture")
            users_name = userinfo.get("given_name", "")
            users_last_name = userinfo.get("family_name", "")
        else:
            return "User email not verified by Google.", 400
        
        # Check if user exists
        user = User.query.filter_by(email=users_email).first()
        
        # Create user if not exists
        if not user:
            user = User(
                username=users_email.split('@')[0],  # Use part before @ as username
                email=users_email,
                password_hash=None,  # OAuth users don't have passwords
                first_name=users_name,
                last_name=users_last_name,
                profile_image_url=picture
            )
            db.session.add(user)
            db.session.commit()
        
        # Log in the user
        login_user(user)
        
        # Redirect to dashboard
        return redirect(url_for("dashboard"))

# Function to check if Google OAuth is configured and available
def is_google_oauth_enabled():
    return google_oauth_configured