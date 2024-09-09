from flask import Flask, request, jsonify, redirect, url_for
import subprocess
import os
import webbrowser

app = Flask(__name__)

# Constants
DEPOT_DOWNLOADER_PATH = "DepotDownloader.exe"  # Ensure this is the correct path to DepotDownloader.exe
REDIRECT_URI = "http://localhost:5000/callback"  # The URL Steam will redirect to after login
STEAM_LOGIN_URL = "https://steamcommunity.com/openid/login"

authenticated_user = {}  # Store authenticated Steam users

# Steam login route
@app.route('/login', methods=['GET'])
def login():
    """Redirects to Steam OpenID login."""
    return redirect(steam_login_url())

def steam_login_url():
    """Generates the Steam OpenID login URL."""
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': REDIRECT_URI,
        'openid.realm': 'http://localhost:5000/',
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select'
    }
    query_string = '&'.join([f'{key}={value}' for key, value in params.items()])
    return f"{STEAM_LOGIN_URL}?{query_string}"

# Callback after Steam login
@app.route('/callback', methods=['GET'])
def callback():
    """Handles Steam OpenID login callback."""
    if 'openid.identity' in request.args:
        steam_id = request.args.get('openid.identity').split('/')[-1]
        authenticated_user['steam_id'] = steam_id  # Store Steam ID for the session
        return f"Login successful! SteamID: {steam_id}"
    else:
        return "Login failed."

# Manifest fetching route
@app.route('/fetch_manifest', methods=['POST'])
def fetch_manifest():
    """Fetches manifest from DepotDownloader."""
    if 'steam_id' not in authenticated_user:
        return jsonify({"status": "error", "message": "User not authenticated"}), 403

    # Extract app_id, depot_id, branch, username, and password
    data = request.get_json()
    app_id = data.get('app_id')
    depot_id = data.get('depot_id')
    branch = data.get('branch', 'public')  # Default to 'public' branch
    username = data.get('username')
    password = data.get('password')

    # Command to run DepotDownloader for fetching the depot manifest
    command = [
        DEPOT_DOWNLOADER_PATH,
        "-app", app_id,
        "-depot", depot_id,
        "-manifest-only",
        "-username", username,
        "-password", password,
        "-beta", branch
    ]

    # Run the command and capture output
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return jsonify({"status": "success", "output": result.stdout}), 200
        else:
            return jsonify({"status": "error", "output": result.stderr}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Open the Steam login page
def open_login_page():
    """Opens the Steam login page in the user's default browser."""
    login_url = steam_login_url()
    webbrowser.open(login_url)

if __name__ == "__main__":
    open_login_page()  # Open the Steam login page in the browser
    app.run(host="0.0.0.0", port=5000)
