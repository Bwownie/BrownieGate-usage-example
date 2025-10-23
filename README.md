```markdown
# BrownieGate Usage Example

This repository is a local developer example that shows how to integrate a web application with the BrownieGate SSO/auth gateway.

Important: BrownieGate is a hosted public service at https://browniegate.xyz — the BrownieGate source is private and you do not host the BrownieGate service yourself. During project setup on the BrownieGate site you will be issued the credentials your application needs.

## What this example demonstrates

- How to launch a local Flask app that uses the BrownieGate client to:
  - decrypt and verify the auth payload returned by BrownieGate,
  - request a cookie token via the BrownieGate API,
  - validate the cookie and bootstrap a server-side session,
  - fetch user data and profile picture from BrownieGate.
- A small protected route (/counter) that demonstrates session usage and simple per-user persistence using SQLite.
- How the client-side and server-side pieces interact for developers running the example on localhost.

## Important: BrownieGate service details

- Hosted domain: https://browniegate.xyz
- BrownieGate provides these values to you when you create/register a project on the site:
  - PROJECT_UUID
  - API_KEY
  - ENCRYPTION_KEY (Fernet key used for payload encryption)
- Your example application should point its BrownieGate client to https://browniegate.xyz (see app configuration).

## Quickstart (local example)

1. Clone this repo and create a virtual environment:

   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate

2. Install dependencies:

   pip install -r requirements.txt

3. Copy and edit credentials:

   cp creds.env.example creds.env

   Replace the placeholders in `creds.env` with the values provided by BrownieGate when you created your project on https://browniegate.xyz:

   - PROJECT_UUID — provided by BrownieGate
   - API_KEY — provided by BrownieGate
   - ENCRYPTION_KEY — provided by BrownieGate (Fernet 32-byte url-safe base64 string)
   - FLASK_SECRET_KEY — local Flask session secret (generate locally)
   - COOKIE_SECURE / SESSION_COOKIE_SECURE — 0 for local HTTP, set to 1 for production HTTPS
   - COOKIE_SAMESITE — Lax (recommended)

   Note: Do NOT commit `creds.env` with real secrets.

4. Confirm the example app is configured to use BrownieGate at `https://browniegate.xyz` (or set BROWNIE_GATE_URL in your local env if you modified the code).

5. Run the example app:

   python app.py

6. Open http://localhost:5000 and click "Login with BrownieGate". This will redirect you to BrownieGate where you sign in, and then be sent back to the example app.

## How the flow works (developer-friendly)

1. The example displays a link to BrownieGate's auth endpoint (using your PROJECT_UUID).
2. After signing in at BrownieGate, the site redirects to `/auth/callback?payload=<encrypted>`.
3. The example uses the BrownieGate client to:
   - decrypt the payload using `ENCRYPTION_KEY`
   - verify the payload with BrownieGate (to ensure it is genuine)
4. On success the example calls `generate_cookie(user_id)` (via the BrownieGate API) to create a server-side cookie row and receives a token value for the browser.
5. The token is saved as a cookie named `auth`. On subsequent requests the app decrypts the cookie (`decrypt_cookie`) and validates it with `validate_cookie`.
6. If validation succeeds, the app creates a Flask session (user_id, username) and shows the protected page.

## Configuration & env variables (creds.env)

- PROJECT_UUID — provided by BrownieGate
- API_KEY — provided by BrownieGate
- ENCRYPTION_KEY — provided by BrownieGate (Fernet key)
- FLASK_SECRET_KEY — app secret for Flask sessions (generate locally)
- COOKIE_SECURE — 0 or 1 (0 for local HTTP)
- COOKIE_SAMESITE — Lax (recommended)
- SESSION_COOKIE_SECURE — 0 or 1

## Developer notes & recommendations

- This example is intended to run on localhost for educational purposes and to illustrate the integration flow with BrownieGate. It is not a production-ready deployment of BrownieGate itself.
- Keep `creds.env` secret. Use the values that BrownieGate provides for your registered project—do not attempt to run a separate BrownieGate instance for production.
- For local development you can keep `COOKIE_SECURE=0`; for production set `COOKIE_SECURE=1` and use HTTPS.
- The example uses SQLite for simplicity; production services should use a managed database and secure secret storage.
- The example client intentionally returns cookie payloads in a simple format for developer convenience; consult BrownieGate docs on the official site for the exact production formats and security guarantees.

## Troubleshooting

- If you see `Invalid payload` during callback, confirm the `ENCRYPTION_KEY` in `creds.env` matches the value shown on the BrownieGate project page.
- If `/counter` keeps redirecting to `/login`, check that the browser has an `auth` cookie and that `FLASK_SECRET_KEY` is set in `creds.env`.
- If API calls time out, ensure browniegate.xyz is reachable and that your API_KEY and PROJECT_UUID are correct.

## Next steps / improvements

- Add an example showing how to register a client in the BrownieGate dashboard (docs on browniegate.xyz).
- Add automated tests using Flask's test client to validate the end-to-end flow.
- Add more documentation on scopes, allowed services, and the exact cookie/payload formats (see BrownieGate docs).

## File overview

- app.py — example Flask application (local developer sample)
- templates/ — login and counter templates
- static/ — CSS, JS, and resources
- creds.env.example — template with placeholders (copy to creds.env)

## License

MIT
```
