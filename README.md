# BrownieGate Usage Example

A simple local-developer example showing how to integrate with the BrownieGate SSO/auth gateway.

This repository contains a tiny Flask web application that demonstrates the end-to-end flow:
- Developer clicks "Login with BrownieGate" which opens the BrownieGate auth page
- BrownieGate returns an encrypted payload (authorization code style) to /auth/callback
- The example verifies the payload, generates a cookie via BrownieGate, sets a local cookie, and creates a session
- A protected /counter page reads the session, fetches a small per-user score from a local sqlite DB, and allows updates via POST

This project is meant for local development and education only — it is NOT intended to be deployed publicly without additional security hardening.

## Features

- Demonstrates BrownieGate client library usage (decrypting/validating payloads, generating cookies, validating cookies, fetching user data and profile picture)
- Minimal Flask example app with a protected route and local sqlite persistence
- creds.env.example with placeholders and notes for local development
- Clear example of cookie/session flow for developers running on localhost

## Quickstart (local development)

1. Clone the repo and create a Python virtual environment

   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows

2. Install dependencies

   pip install -r requirements.txt

3. Copy the example credentials file and fill values

   cp creds.env.example creds.env

   - PROJECT_UUID: project id from your BrownieGate project
   - API_KEY: API key for your project
   - ENCRYPTION_KEY: Fernet key (32 urlsafe base64 bytes):  From your brownieGate project
   - FLASK_SECRET_KEY: random hex or token for Flask sessions (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - COOKIE_SECURE / SESSION_COOKIE_SECURE: use `0` for localhost, `1` for HTTPS
   - COOKIE_SAMESITE: Lax (recommended)

4. Start a local BrownieGate instance (if you have it) or point BROWNIE_GATE_URL in creds.env at the running gate.

5. Run the example app

   python app.py

6. Open http://localhost:5000 in your browser and click "Login with BrownieGate".

## Environment variables (creds.env)

- PROJECT_UUID: UUID for your BrownieGate project
- API_KEY: API key for your project
- ENCRYPTION_KEY: Fernet key used to encrypt/decrypt payloads and cookies
- FLASK_SECRET_KEY: Secret used by Flask to sign the session cookie
- COOKIE_SECURE: 0 or 1 (set 1 in production with HTTPS)
- COOKIE_SAMESITE: Lax (recommended)
- SESSION_COOKIE_SECURE: 0 or 1

## How the flow works (developer-friendly)

1. The example provides a link to BrownieGate's /gate/auth endpoint with the project_uuid.
2. After a successful login, BrownieGate redirects back to `/auth/callback?payload=<encrypted>`.
3. The example uses the BrownieGate client to `decrypt_payload` and `verify_payload`.
4. On success the example calls `generate_cookie(user_id)` to create a server-side cookie row and receives a token to set in the browser.
5. The token is stored as a cookie named `auth`. On subsequent requests the site attempts to decrypt the cookie (`decrypt_cookie`) and validate it with `validate_cookie`.
6. If validation succeeds the app boots a Flask session with the user's data (username, user_id) and shows the protected counter page.

## Developer notes & recommendations

- This example intentionally favors clarity over production hardening. If you plan to use BrownieGate or this example in a public environment, apply security best practices: use TLS, set `COOKIE_SECURE=1`, store secrets in a secret manager, use Argon2 for passwords, implement rate limiting and PKCE/OAuth2 standard endpoints.
- The example stores example data in a local sqlite DB (`data.db`) with a simple `data(user_id PK, score)` table. The DB is created automatically on first run.
- The client library intentionally returns cookie payloads in a simple format for developers; see `browniegate` client for details.
- Use `request.get_json()` for POST bodies; the example already adopts this for `/update_count`.

## File overview

- app.py — the Flask example application
- templates/ — HTML templates for the login and counter pages
- static/ — CSS, JS, and static resources
- creds.env.example — env template for local development

## Troubleshooting

- If you see `Invalid payload` on callback, ensure your `ENCRYPTION_KEY` matches the BrownieGate instance's key for your project and that the payload wasn't tampered with.
- If `/counter` keeps redirecting to `/login`, check the browser cookie `auth` is present and that `FLASK_SECRET_KEY` is set so the server can create sessions.
- If BrownieGate API calls time out, ensure the BrownieGate service is running and reachable at the configured URL.

## Next steps / improvements

- Add a short README section showing how to register a demo client on BrownieGate
- Add an automated test that uses Flask's test client to validate the callback->session->counter flow
- Add more detailed docs on cookie formats and the BrownieGate client API

## License

MIT
