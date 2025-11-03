# 🍫 BrownieGate — Usage Example

A compact, local developer example showing how to integrate a web application with the hosted BrownieGate SSO/auth gateway (https://browniegate.xyz).  
BrownieGate is a hosted service — you do not run the BrownieGate production service locally. When you register a project on BrownieGate you will be issued the credentials required to integrate your app.

---

## Quick links
- Website: https://browniegate.xyz

---

## What this repo is
This repository contains a tiny Flask app demonstrating the core integration flow:

- Redirect to BrownieGate to sign in
- BrownieGate redirects back to `/auth/callback` with an encrypted payload
- Example app decrypts and verifies the payload via the BrownieGate client
- Example app requests a cookie token from BrownieGate, sets a local cookie and bootstraps a server-side session
- Protected route (`/counter`) shows how to use session data and persist a tiny per-user value in SQLite

This is a developer example intended to run on localhost for learning and experimentation only.

---

## Table of contents
- Quickstart
- Configuration (creds.env)
- How the flow works
- Troubleshooting
- Developer notes & recommendations
- Files
- License

---

## Quickstart (local development)

1. Clone this repo and create a virtual environment
```bash
git clone https://github.com/Bwownie/BrownieGate-usage-example.git
cd BrownieGate-usage-example
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Copy the example credentials and fill values
```bash
cp creds.env.example creds.env
```
Edit `creds.env` and paste in the credentials provided by BrownieGate (when you created your project at https://browniegate.xyz):
- `PROJECT_UUID` — provided by BrownieGate
- `API_KEY` — provided by BrownieGate
- `ENCRYPTION_KEY` — provided by BrownieGate (Fernet 32-byte url-safe base64) — BrownieGate supplies this when you create your project
- `FLASK_SECRET_KEY` — local Flask session secret (generate locally)
- `COOKIE_SECURE` / `SESSION_COOKIE_SECURE` — `0` for local HTTP, `1` for HTTPS
- `COOKIE_SAMESITE` — `Lax` is recommended

> Important: do NOT commit your `creds.env` to source control.

4. Run the example app
```bash
python app.py
```

5. Open http://localhost:5000 and click **Login with BrownieGate** to begin the demo flow.

---

## Configuration (creds.env)

| Key                 | Purpose |
|--------------------:|---------|
| PROJECT_UUID        | UUID for your BrownieGate project (from browniegate.xyz) |
| API_KEY             | API key for your project (from browniegate.xyz) |
| ENCRYPTION_KEY      | Fernet key used for payload encryption (provided by BrownieGate) |
| FLASK_SECRET_KEY    | Flask session signing secret (generate locally) |
| COOKIE_SECURE       | 0 or 1 (0 = local HTTP; 1 = HTTPS) |
| COOKIE_SAMESITE     | SameSite value for cookies (e.g., `Lax`) |
| SESSION_COOKIE_SECURE | 0 or 1 |

How to generate keys locally:
- Flask secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## How the flow works (developer-friendly)

1. The app links to BrownieGate's auth endpoint (includes your `PROJECT_UUID`).
2. After successful sign-in on BrownieGate, the user is redirected to:
   ```
   /auth/callback?payload=<encrypted>
   ```
3. The app uses the BrownieGate client to:
   - `decrypt_payload(payload)` using `ENCRYPTION_KEY`
   - `verify_payload(...)` to confirm the payload authenticity
4. App calls `generate_cookie(user_id)` (BrownieGate API) to create a server-side cookie row and receives a token to set in the browser.
5. The token is stored as an `auth` cookie. On subsequent requests the app:
   - decrypts the cookie (`decrypt_cookie`) to obtain `user_id` and `cookie_hash`
   - calls `validate_cookie(user_id, cookie_hash)` to confirm validity
6. If validated, the app bootstraps a Flask session (user_id, username) and serves the protected page.

---

## Troubleshooting

- **Invalid payload** during callback: ensure `ENCRYPTION_KEY` in `creds.env` matches the key shown on your BrownieGate project page.
- **Stuck on /login** after callback: check the browser has an `auth` cookie and that `FLASK_SECRET_KEY` is set in `creds.env`.
- **API calls time out**: verify `browniegate.xyz` is reachable and your `PROJECT_UUID` and `API_KEY` are correct.

---

## Developer notes & recommendations

- This example focuses on clarity. If you plan to integrate BrownieGate in production, follow security best practices:
  - Use TLS (HTTPS) and set `COOKIE_SECURE=1`
  - Use a secure secret manager for keys
  - Use Argon2 for password storage (if you manage passwords locally)
  - Implement rate limiting, PKCE and OAuth2/OIDC flows according to your client needs
- The example uses SQLite for simplicity. Production services should use a managed DB.
- BrownieGate provides the Fernet `ENCRYPTION_KEY` for your project; do not invent or substitute your own for production use unless explicitly instructed by the BrownieGate dashboard/docs.

---

## Files

- `app.py` — Flask example application
- `templates/` — login and counter templates
- `static/` — CSS, JS, and resources
- `creds.env.example` — template (copy to `creds.env` and fill)

---

## License

MIT
