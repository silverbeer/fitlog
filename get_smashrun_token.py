#!/usr/bin/env python3
"""
Script to get new Smashrun OAuth tokens.
This will guide you through the OAuth flow to get new access and refresh tokens.
"""

import os
import webbrowser
from urllib.parse import urlencode
from dotenv import load_dotenv, set_key
from pathlib import Path

# Load existing .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

client_id = os.getenv("SMASHRUN_CLIENT_ID")
client_secret = os.getenv("SMASHRUN_CLIENT_SECRET")

if not client_id or not client_secret:
    print("❌ Missing SMASHRUN_CLIENT_ID or SMASHRUN_CLIENT_SECRET in .env file")
    exit(1)

# OAuth endpoints
auth_base_url = "https://secure.smashrun.com/oauth2/authenticate"
token_url = "https://secure.smashrun.com/oauth2/token"

# Step 1: Direct user to authorize
print("🏃 Smashrun OAuth Token Setup")
print("=" * 50)
print()
print("This script will help you get new Smashrun API tokens.")
print()
print("Step 1: Authorize the application")
print("-" * 30)

# For Smashrun, we need to use 'code' response type for refresh tokens
params = {
    'client_id': client_id,
    'response_type': 'code',
    'redirect_uri': 'https://localhost:8080/callback',  # You'll need to manually copy the code
    'scope': 'read_activity'  # Adjust scope as needed
}

auth_url = f"{auth_base_url}?{urlencode(params)}"

print(f"Opening browser to: {auth_url}")
print()
print("After authorizing, you'll be redirected to a URL like:")
print("https://localhost:8080/callback?code=YOUR_CODE")
print()
print("Copy the 'code' parameter value from the URL.")
print()

webbrowser.open(auth_url)

# Step 2: Get the authorization code
print("Step 2: Exchange code for tokens")
print("-" * 30)
auth_code = input("Enter the authorization code from the URL: ").strip()

if not auth_code:
    print("❌ No authorization code provided")
    exit(1)

# Step 3: Exchange code for tokens
print()
print("Exchanging authorization code for tokens...")

import requests

token_data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'grant_type': 'authorization_code',
    'code': auth_code,
    'redirect_uri': 'https://localhost:8080/callback'
}

try:
    response = requests.post(token_url, data=token_data)
    response.raise_for_status()
    
    tokens = response.json()
    
    if 'access_token' in tokens:
        print("✅ Successfully obtained tokens!")
        print()
        
        # Update .env file
        set_key(env_path, "SMASHRUN_ACCESS_TOKEN", tokens['access_token'])
        
        if 'refresh_token' in tokens:
            set_key(env_path, "SMASHRUN_REFRESH_TOKEN", tokens['refresh_token'])
            print("✅ Refresh token saved - automatic token refresh enabled!")
        else:
            print("⚠️  No refresh token received - you'll need to re-authenticate when token expires")
        
        if 'expires_in' in tokens:
            import time
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(seconds=tokens['expires_in'])
            set_key(env_path, "SMASHRUN_TOKEN_EXPIRES", expires_at.isoformat())
            print(f"📅 Token expires at: {expires_at}")
        
        print()
        print("Your .env file has been updated with the new tokens.")
        print("You can now use: fitlog import-smashrun")
    else:
        print("❌ No access token in response")
        print(f"Response: {tokens}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to exchange code for tokens: {e}")
    if hasattr(e.response, 'text'):
        print(f"Response: {e.response.text}")
    exit(1)