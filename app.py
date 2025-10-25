from flask import Flask, render_template, redirect, url_for, request, session, make_response, jsonify
from browniegate import *   # brownieGate client library
import os
from dotenv import load_dotenv
import sqlite3
from pathlib import Path

# Load local development environment variables from creds.env
# See creds.env.example in the repo for required variables and example values.
load_dotenv(dotenv_path="creds.env")

# Configuration from environment (developers should set these in creds.env)
PROJECT_UUID = os.getenv('PROJECT_UUID', '')
API_KEY = os.getenv('API_KEY', '')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')
BROWNIE_GATE_URL = os.getenv('BROWNIE_GATE_URL', 'http://10.8.0.3:5001')

# App secret key for Flask sessions (do NOT commit real secrets)
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
# Cookie flags configurable for local dev; set COOKIE_SECURE=1 in creds.env for HTTPS/prod
COOKIE_SECURE = bool(int(os.getenv('COOKIE_SECURE', '0')))
COOKIE_SAMESITE = os.getenv('COOKIE_SAMESITE', 'Lax')  # Lax is a sensible default

# Flask app
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY or os.urandom(24)
# Session cookie defaults (safe defaults for examples)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE=COOKIE_SAMESITE,
)

# Local SQLite DB path for example data
DB_PATH = Path("data.db")

def ensure_db():
    """
    Ensure the example database and table exist.
    user_id is the primary key so we can use INSERT OR IGNORE semantics.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS data (
                user_id TEXT PRIMARY KEY,
                score INTEGER DEFAULT 0
            );
        """)
        conn.commit()

# Make sure DB exists before handling requests
ensure_db()

# Initialize the BrownieGate client wrapper for example usage
gate = brownieGate(api_key=API_KEY, project_uuid=PROJECT_UUID, encryption_key=ENCRYPTION_KEY, url=BROWNIE_GATE_URL, debug=True)

# ---------- Helper functions (small, easy-to-follow) ----------

def setup_user_in_database(user_id: str):
    """
    Ensure a data row exists for this user in the local example DB.
    We use INSERT OR IGNORE to avoid race conditions and keep the function simple.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO data (user_id, score) VALUES (?, ?)", (user_id, 0))
        conn.commit()

def setup_user_session(user_id: str):
    """
    Populate the Flask session with basic user info fetched from BrownieGate.
    Demonstrates how you can bootstrap server-side session state after auth.
    """
    try:
        success, data = gate.get_user_data(user_id)
    except Exception:
        success = False
        data = {}
    if success:
        session['user_id'] = user_id
        session['username'] = data.get('username')

def get_user_score(user_id: str):
    """
    Load the user's saved score into the session so the view can render it.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT score FROM data WHERE user_id = ?", (user_id,))
        result = cur.fetchone()
        if result:
            session['score'] = result[0]
        else:
            session['score'] = 0

# ---------- Routes (login flow + small protected example) ----------

@app.route("/")
def root():
    return redirect(url_for('login'))

@app.route("/login")
def login():
    """
    Login page:
    - If a server-side session exists -> redirect to /counter
    - If an 'auth' cookie exists -> try to decrypt & validate it, bootstrap session and redirect on success
    - If cookie is invalid/unparseable -> delete cookie and render login page
    - Otherwise render login page (the template includes popup JS)
    """
    # 1) If session already present, go directly to protected page
    if session.get('user_id'):
        return redirect(url_for('counter'))

    # 2) If an auth cookie exists, validate it before redirecting
    token = request.cookies.get('auth')
    if token:
        try:
            user_id, cookie_hash = gate.decrypt_cookie(token)
        except Exception:
            # Cookie is malformed / cannot be decrypted -> remove cookie and show login
            resp = make_response(render_template("login.html", brownie_gate_url=f'{BROWNIE_GATE_URL}/gate/auth?project_uuid={PROJECT_UUID}'))
            resp.delete_cookie('auth')
            return resp

        # If decrypt succeeded, validate with BrownieGate
        try:
            if gate.validate_cookie(user_id, cookie_hash):
                # Valid cookie -> populate session and continue
                setup_user_session(user_id)
                return redirect(url_for('counter'))
            else:
                # Invalid/expired cookie -> delete and show login
                resp = make_response(render_template("login.html", brownie_gate_url=f'{BROWNIE_GATE_URL}/gate/auth?project_uuid={PROJECT_UUID}'))
                resp.delete_cookie('auth')
                return resp
        except Exception:
            # If validation call fails (network/Gate error), prefer showing login and removing cookie
            resp = make_response(render_template("login.html", brownie_gate_url=f'{BROWNIE_GATE_URL}/gate/auth?project_uuid={PROJECT_UUID}'))
            resp.delete_cookie('auth')
            return resp

    # 3) No session and no cookie -> render login link (popup-enabled)
    return render_template("login.html", brownie_gate_url=f'{BROWNIE_GATE_URL}/gate/auth?project_uuid={PROJECT_UUID}')

@app.route("/auth/callback")
def callback():
    """
    Callback endpoint BrownieGate redirects to after the developer logs in on the gate.
    Expected query param: payload
      - decrypt payload with gate.decrypt_payload()
      - verify payload with gate.verify_payload()
      - generate a cookie and set it on the response
      - create example DB record and session
    For the popup flow we return a small HTML page that posts a message to window.opener
    and then closes the popup. The cookie is set on this response so the main window
    (same origin) will have the cookie on subsequent requests.
    """
    payload = request.args.get("payload")
    if not payload:
        return "Missing payload", 400

    try:
        # decrypt + verify
        success, user_id = gate.verify_payload(gate.decrypt_payload(payload))
    except Exception:
        # In a local example it's helpful to show a simple error; in real apps log this server-side.
        return "Invalid payload or verification error", 400

    if not success:
        return "Authentication failed", 401

    # Generate cookie token via the example client (may return bytes or str)
    token = gate.generate_cookie(user_id)
    token_str = token.decode() if isinstance(token, bytes) else str(token)

    # Set cookie on response. Instead of redirecting (full window), return the popup template
    resp = make_response(render_template('auth_callback_popup.html'))
    resp.set_cookie(
        'auth',
        token_str,
        max_age=60*60*24*7,     # one week
        secure=COOKIE_SECURE,   # set to True for HTTPS production
        httponly=True,          # prevents JavaScript from reading the cookie (recommended)
        samesite=COOKIE_SAMESITE
    )

    # Ensure an example row exists for this user and set up session
    setup_user_in_database(user_id)
    setup_user_session(user_id)

    return resp

@app.route("/counter")
def counter():
    """
    Protected example page. If no server-side session exists, attempt to validate the
    auth cookie (cookie contains user_id & cookie_hash when decrypted by gate.decrypt_cookie).
    If validation succeeds, set up session and render the page.
    """
    # If the session already has the user, render immediately
    if not session.get('user_id'):
        token = request.cookies.get('auth')
        if not token:
            # No auth cookie -> redirect to login
            return redirect(url_for('login'))

        try:
            # decrypt_cookie returns (user_id, cookie_hash)
            user_id, cookie_hash = gate.decrypt_cookie(token)
        except Exception:
            # Decrypt failed -> treat as unauthenticated
            return redirect(url_for('login'))

        # Validate cookie with BrownieGate backend
        try:
            if not gate.validate_cookie(user_id, cookie_hash):
                return redirect(url_for('login'))
        except Exception:
            # If the Gate API is unreachable treat as unauthenticated in this demo
            return redirect(url_for('login'))

        # Populate Flask session
        setup_user_session(user_id)

    # Ensure user's score is loaded for the view
    if not session.get('score'):
        get_user_score(session['user_id'])

    return render_template('counter.html')

@app.route('/update_count', methods=['POST'])
def update_count():
    """
    Store the counter value in the local DB. Client should POST JSON: { "score": <int> }.
    Uses request.get_json for robust parsing and returns proper HTTP status codes on errors.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "invalid json"}), 400

    # basic validation and normalization
    try:
        score = int(data.get('score', 0))
    except Exception:
        return jsonify({"status": "error", "message": "invalid score"}), 400

    # Save in session for immediate access
    session['score'] = score

    # Persist in local DB
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('UPDATE data SET score = ? WHERE user_id = ?', (score, session['user_id']))
        if cur.rowcount == 0:
            cur.execute('INSERT INTO data (user_id, score) VALUES (?, ?)', (session['user_id'], score))
        conn.commit()

    return jsonify({"status": "success", "score": score})

@app.route('/logout')
def logout():
    """
    Log the user out of this example:
      - tell BrownieGate to remove server-side cookie rows (gate.remove_cookie)
      - clear Flask session and delete the browser cookie
    """
    # Only call remove_cookie if we have a user_id; this keeps example calls minimal
    user_id = session.get('user_id')
    if user_id:
        try:
            gate.remove_cookie(user_id)
        except Exception:
            # Ignore removal errors for this local demo
            pass

    session.clear()
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('auth')
    return resp

@app.route('/get_pfp/me')
def get_pfp():
    """
    Example helper route for client-side code to fetch the user's profile picture (pfp).
    Returns JSON { success: True, pfp: <data-url> } when session is present.
    """
    if session.get('user_id'):
        try:
            pfp = gate.get_pfp(session.get('user_id'))
        except Exception:
            pfp = None

        return {'success': True, 'pfp': pfp or None}
    else:
        return {'success': False}, 401

# Simple health endpoint useful for quick verification that the example app is running
@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # Local development: debug True is convenient. Don't use debug=True on public servers.
    app.run(debug=True, host="localhost", port=5000)