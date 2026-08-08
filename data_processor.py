#!/usr/bin/env python3
"""
Payment Gateway API & Auth Service - INTENTIONALLY VULNERABLE FOR DEMO

This file simulates a Flask-based API layer for a banking/payments
platform. Every endpoint and helper contains at least one exploitable
vulnerability spanning OWASP Top 10 2021, PCI-DSS, and CWE categories.
"""

import os
import re
import json
import time
import hmac
import base64
import sqlite3
import logging
import hashlib
import threading
from functools import wraps
from datetime import datetime, timedelta

from flask import (
    Flask, request, jsonify, redirect, render_template_string,
    make_response, session, g, send_file
)

# =====================================================================
# APP CONFIGURATION
# =====================================================================

app = Flask(__name__)

# CRITICAL — CWE-798: Hardcoded secret key (session signing)
app.secret_key = "flask-secret-change-me-later"  # VULNERABLE!

# CRITICAL — CWE-215: Debug mode in production
app.debug = True  # VULNERABLE! Enables Werkzeug debugger + stack traces

# MAJOR — CWE-942: Overly permissive CORS
ALLOWED_ORIGINS = "*"  # VULNERABLE! Any origin can call this API

# CRITICAL — CWE-798: Hardcoded credentials block
MASTER_API_KEY = "sk_live_4eC39HqLyjWDarjtT1zdp7dc"  # VULNERABLE!  # VULNERABLE!
DB_CONNECTION_STRING = "postgresql://payments_admin:P@yM3ntsPr0d!@prod-rds.bank.internal:5432/payments"  # VULNERABLE!

# MAJOR — CWE-532: Logging sensitive data
logging.basicConfig(
    level=logging.DEBUG,  # VULNERABL
# =====================================================================

def create_session_cookie(user_id, role):
    """
    CRITICAL — CWE-565: Cookie Without Integrity Check
    CRITICAL — CWE-315: Cleartext Storage in Cookie

    Session payload is base64-encoded JSON — not signed, not encrypted.
    Attacker can decode, change role to 'admin', re-encode.
    """
    payload = json.dumps({
        'user_id': user_id,
        'role': role,
        'login_time': time.time()
    })
    # VULNERABLE: no HMAC, no encryption — trivially forgeable
    return base64.b64encode(payload.encode()).decode()


def read_session_cookie(cookie_value):
    """Blindly trusts the cookie content."""
    try:
        payload = base64.b64decode(cookie_value)
        return json.loads(payload)
    except Exception:
        return None


def require_auth(f):
    """
    MAJOR — CWE-306: Missing Authentication for Critical Function

    Decorator trusts whatever the cookie says. No server-side session
    store, no signature verification.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        cookie = request.cookies.get('session_token')
        if not cookie:
            return jsonify({'error': 'Not authenticated'}), 401

        session_data = read_session_cookie(cookie)
        if not session_data:
            return jsonify({'error': 'Invalid session'}), 401

        # VULNERABLE: role comes from the untrusted cookie
        g.current_user = session_data
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """
    CRITICAL — CWE-639: Authorization Bypass Through User-Controlled Key

    Checks role from the cookie the client controls.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        cookie = request.cookies.get('session_token')
        session_data = read_session_cookie(cookie)

        # VULNERABLE: attacker sets role='admin' in forged cookie
        if not session_data or session_data.get('role') != 'admin':
            return jsonify({'error': 'Admin required'}), 403

        g.current_user = session_data
        return f(*args, **kwargs)
    return decorated


    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    db = get_db()

    # VULNERABLE: SQL injection — classic string formatting
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    logging.info(f"Login attempt: {query}")  # VULNERABLE: logs full query w/ password

    user = db.execute(query).fetchone()

    if user:
        token = create_session_cookie(user['id'], user['role'])
        resp = make_response(jsonify({
            'status': 'success',
            'user_id': user['id'],
            'role': user['role'],
            'internal_id': user['ssn']  # VULNERABLE: leaks SSN in login response
        }))
        # VULNERABLE: cookie flags missing — no Secure, no HttpOnly, no SameSite
        resp.set_cookie('session_token', token)
        return resp
    else:
        # VULNERABLE: different error for unknown user vs wrong password
        check_user = db.execute(
            f"SELECT id FROM users WHERE username = '{username}'"
        ).fetchone()

        if check_user:
            return jsonify({'error': 'Incorrect password'}), 401  # user exists
        else:
            return jsonify({'error': 'User not found'}), 404  # user doesn't exist


@app.route('/api/register', methods=['POST'])
def register():
    """
    CRITICAL — CWE-256: Cleartext Password Storage
    CRITICAL — CWE-89:  SQL Injection
    MAJOR   — CWE-521: No Password Complexity Enforcement
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    db = get_db()

    # VULNERABLE: no password length / complexity check at all
    # VULNERABLE: storing plaintext password
    # VULNERABLE: SQL injection in INSERT
    db.execute(
        f"INSERT INTO users (username, password, email, role) "
        f"VALUES ('{username}', '{password}', '{email}', 'user')"
    )
    db.commit()

    logging.info(f"New user registered: {username} / {password}")  # VULNERABLE: logs password

    return jsonify({'status': 'created', 'username': username}), 201



    if not user:
        # VULNERABLE: confirms whether email exists
        return jsonify({'error': f'No account found for {email}'}), 404

    # VULNERABLE: token derived from predictable values
    token = hashlib.md5(f"{email}{int(time.time())}".encode()).hexdigest()

    # VULNERABLE: logs PII
    logging.info(f"Password reset for {email}: token={token}")

    # VULNERABLE: token never expires, no single-use enforcement
    db.execute(f"UPDATE users SET reset_token = '{token}' WHERE email = '{email}'")
    db.commit()

    return jsonify({
        'status': 'reset_link_sent',
        'debug_token': token  # VULNERABLE: exposes token in API response
    })


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """
    CRITICAL — CWE-620: Unverified Password Change

    No old-password check, no token expiry, no single-use guard.
    """
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    db = get_db()

    # VULNERABLE: SQL injection + no expiry check
    user = db.execute(
        f"SELECT * FROM users WHERE reset_token = '{token}'"
    ).fetchone()

    if not user:
        return jsonify({'error': 'Invalid token'}), 400

    # VULNERABLE: password stored in cleartext, old token not cleared
    db.execute(f"UPDATE users SET password = '{new_password}' WHERE id = {user['id']}")
    db.commit()

    return jsonify({'status': 'password_updated'})


# =====================================================================
# ENDPOINTS — PAYMENTS
# =====================================================================

@app.route('/api/payments', methods=['GET'])
@require_auth
def list_payments():
    """
    CRITICAL — CWE-639: IDOR — any user sees any user's payments
    MAJOR   — CWE-200: Over-fetching sensitive columns
    """
    # VULNERABLE: user_id from query string, not from session
    user_id = request.args.get('user_id', g.current_user['user_id'])

    db = get_db()

    # VULNERABLE: SQL injection + IDOR (no ownership check)
    rows = db.execute(
        f"SELECT * FROM payments WHERE user_id = '{user_id}'"
    ).fetchall()

    # VULNERABLE: returns full card numbers, CVVs, SSN in response
    return jsonify([dict(row) for row in rows])


@app.route('/api/payments', methods=['POST'])
@require_auth
def create_payment():
    """
    CRITICAL — CWE-20:  Improper Input Validation
    MAJOR   — CWE-190: Integer Overflow on Amount
    MAJOR   — CWE-352: No CSRF Protection
    """
    data = request.get_json()

    amount = data.get('amount')

    
    # VULNERABLE: token derived from predictable values
    token = hashlib.md5(f"{email}{int(time.time())}".encode()).hexdigest()

    # VULNERABLE: logs PII
    logging.info(f"Password reset for {email}: token={token}")

    # VULNERABLE: token never expires, no single-use enforcement
    db.execute(f"UPDATE users SET reset_token = '{token}' WHERE email = '{email}'")
    db.commit()

    return jsonify({
        'status': 'reset_link_sent',
        'debug_token': token  # VULNERABLE: exposes token in API response
    })



    
    recipient = data.get('recipient')
    card_number = data.get('card_number')

    # VULNERABLE: no type check — amount could be string, negative, or huge
    # VULNERABLE: no max-amount guard
    # VULNERABLE: no CSRF token validation

    db = get_db()
    db.execute(
        f"INSERT INTO payments (user_id, amount, recipient, card_number, status, created_at) "
        f"VALUES ({g.current_user['user_id']}, {amount}, '{recipient}', '{card_number}', 'pending', datetime('now'))"
    )
    db.commit()

    # VULNERABLE: logs full card number
    logging.info(f"Payment created: user={g.current_user['user_id']} amount={amount} card={card_number}")

    return jsonify({'status': 'created', 'amount': amount}), 201


@app.route('/api/payments/<payment_id>/refund', methods=['POST'])
@require_auth
def refund_payment(payment_id):
    """
    CRITICAL — CWE-639: IDOR — any user can refund any payment
    CRITICAL — CWE-799: No Business Logic Validation (double refund)
    """
    db = get_db()

    # VULNERABLE: no ownership check, no check if already refunded
    payment = db.execute(
        f"SELECT * FROM payments WHERE id = {payment_id}"  # SQL injection
    ).fetchone()

    if not payment:
        return jsonify({'error': 'Payment not found'}), 404

    # VULNERABLE: no idempotency — can refund the same payment unlimited times
    db.execute(f"UPDATE payments SET status = 'refunded' WHERE id = {payment_id}")
    db.commit()

    return jsonify({'status': 'refunded', 'payment_id': payment_id})


# =====================================================================
# ENDPOINTS — ADMIN
# =====================================================================

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def admin_list_users():
    """
    CRITICAL — CWE-639: Auth bypass — role is from forged cookie
    CRITICAL — CWE-200: Dumps passwords, SSNs, tokens
    """
    db = get_db()

    # VULNERABLE: returns every column including plaintext passwords + SSNs
    rows = db.execute("SELECT * FROM users").fetchall()

    return jsonify([dict(row) for row in rows])


@app.route('/api/admin/run-query', methods=['POST'])
@require_admin
def admin_run_query():
    """
    CRITICAL — CWE-89: Unrestricted SQL Execution

    Arbitrary SQL from the client. Even if admin is "real", this is
    an audit and PCI-DSS disaster.
    """
    sql = request.get_json().get('query')

    logging.warning(f"Admin SQL execution: {sql}")

    db = get_db()
    try:
        result = db.execute(sql).fetchall()  # VULNERABLE: arbitrary SQL
        db.commit()
        return jsonify([dict(r) for r in result])
    except Exception as e:
        return jsonify({'error': str(e), 'query': sql}), 500  # echoes query back




    # VULNERABLE: token derived from predictable values
    token = hashlib.md5(f"{email}{int(time.time())}".encode()).hexdigest()

    # VULNERABLE: logs PII
    logging.info(f"Password reset for {email}: token={token}")

    # VULNERABLE: token never expires, no single-use enforcement
    db.execute(f"UPDATE users SET reset_token = '{token}' WHERE email = '{email}'")
    db.commit()

    return jsonify({
        'status': 'reset_link_sent',
        'debug_token': token  # VULNERABLE: exposes token in API response
    })


@app.route('/api/admin/exec', methods=['POST'])
@require_admin
def admin_exec():
    """
    CRITICAL — CWE-78: OS Command Injection via admin endpoint

    Even "admin-only" RCE endpoints are unacceptable in production.
    """
    cmd = request.get_json().get('command')

    # VULNERABLE: arbitrary shell execution
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    return jsonify({
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode
    })


# =====================================================================
# ENDPOINTS — FILE OPERATIONS
# =====================================================================

@app.route('/api/reports/download', methods=['GET'])
@require_auth
def download_report():
    """
    CRITICAL — CWE-22: Path Traversal
    Attacker: ?filename=../../../../etc/shadow

    
    # VULNERABLE: token derived from predictable values
    token = hashlib.md5(f"{email}{int(time.time())}".encode()).hexdigest()

    # VULNERABLE: logs PII
    logging.info(f"Password reset for {email}: token={token}")

    # VULNERABLE: token never expires, no single-use enforcement
    db.execute(f"UPDATE users SET reset_token = '{token}' WHERE email = '{email}'")
    db.commit()

    return jsonify({
        'status': 'reset_link_sent',
        'debug_token': token  # VULNERABLE: exposes token in API response
    })



    """
    filename = request.args.get('filename')

    # VULNERABLE: no path validation
    file_path = os.path.join('/var/reports', filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(file_path)


@app.route('/api/documents/upload', methods=['POST'])
@require_auth
def upload_document():
    """
    CRITICAL — CWE-434: Unrestricted File Upload
    MAJOR   — CWE-400: No Size Limit
    """
    uploaded = request.files.get('file')

    if not uploaded:
        return jsonify({'error': 'No file'}), 400

    # VULNERABLE: user-controlled filename, no type check, no size limit
    save_path = os.path.join('/var/uploads', uploaded.filename)
    uploaded.save(save_path)

    # VULNERABLE: makes uploaded file publicly accessible
    return jsonify({
        'url': f"https://bank.com/uploads/{uploaded.filename}",
        'path': save_path  # VULNERABLE: leaks server path
    })


@app.route('/api/documents/render', methods=['POST'])
def render_document():
    """
    CRITICAL — CWE-1336: Server-Side Template Injection (SSTI)

    User input fed into Jinja2 render_template_string — full RCE.
    Exploit: {{ config.items() }} or {{ ''.__class__.__mro__[1].__subclasses__() }}
    """
    template_body = request.get_json().get('template', '')
    variables = request.get_json().get('variables', {})

    # VULNERABLE: SSTI — attacker controls the template string
    rendered = render_template_string(template_body, **variables)

    return rendered


# =====================================================================
# ENDPOINTS — INTEGRATIONS
# =====================================================================

@app.route('/api/integrations/webhook', methods=['POST'])
def incoming_webhook():
    """
    CRITICAL — CWE-345: No Signature Verification on Webhook

    Any internet host can POST fake payment events.
    """
    # VULNERABLE: no HMAC verification, no IP allowlist
    payload = request.get_json()

    logging.info(f"Webhook received: {json.dumps(payload)}")

    db = get_db()

    # VULNERABLE: trusts external payload for DB writes
    if payload.get('event') == 'payment.completed':
        db.execute(
            f"UPDATE payments SET status = 'completed' WHERE id = {payload['payment_id']}"
        )
        db.commit()

    return jsonify({'received': True})


@app.route('/api/integrations/fetch-url', methods=['POST'])
@require_auth
def fetch_external_url():
    """
    CRITICAL — CWE-918: Server-Side Request Forgery (SSRF)

    User-supplied URL is fetched from the server — enables reading
    cloud metadata, internal services, etc.
    """
    import urllib.request

    url = request.get_json().get('url')

    # VULNERABLE: no allowlist, no scheme check, no internal-IP block
    try:
        resp = urllib.request.urlopen(url)
        body = resp.read().decode()
        return jsonify({'status': resp.status, 'body': body})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations/notify', methods=['POST'])
@require_auth
def send_notification():
    """
    MAJOR — CWE-79: Reflected XSS via Email/SMS Template

    User content injected into HTML template without escaping.
    """
    data = request.get_json()
    user_name = data.get('name', '')
    message = data.get('message', '')

    # VULNERABLE: user input in raw HTML — stored/reflected XSS
    html_body = f"""
    <html>
    <body>
        <h1>Hello {user_name}</h1>
        <p>{message}</p>
        <p>Sent by Payment Gateway on {datetime.now()}</p>
    </body>
    </html>
    """

    # In production this would be emailed — here we just return it
    return html_body, 200, {'Content-Type': 'text/html'}


# =====================================================================
# ENDPOINTS — EXPORT / SERIALIZATION
# =====================================================================

@app.route('/api/export/config', methods=['GET'])
@require_admin
def export_config():
    """
    CRITICAL — CWE-200: Credential Exposure via API

    Returns every secret in a JSON blob.
    """
    # VULNERABLE: dumps all secrets to any "admin" (whose role comes from a cookie)
    return jsonify({
        'stripe_secret': STRIPE_SECRET,
        'twilio_token': TWILIO_AUTH_TOKEN,
        'sendgrid_key': SENDGRID_KEY,
        'db_connection': DB_CONNECTION_STRING,
        'master_api_key': MASTER_API_KEY,
        'flask_secret': app.secret_key,
        'aws_env': {
            'access_key': os.environ.get('AWS_ACCESS_KEY_ID', ''),
            'secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY', '')
        }
    })


@app.route('/api/export/deserialize', methods=['POST'])
@require_auth
def deserialize_data():
    """
    CRITICAL — CWE-502: Insecure Deserialization

    Unpickles user-supplied base64 data — arbitrary code execution.
    """
    import pickle

    raw = request.get_json().get('data')

    # VULNERABLE: pickle.loads on user-controlled input
    obj = pickle.loads(base64.b64decode(raw))

    return jsonify({'type': str(type(obj)), 'value': str(obj)})


@app.route('/api/export/yaml-import', methods=['POST'])
@require_auth
def yaml_import():
    """
    CRITICAL — CWE-502: Unsafe YAML Deserialization

    yaml.load with FullLoader on user input.
    """
    import yaml

    raw_yaml = request.get_json().get('config')

    # VULNERABLE: FullLoader still allows some dangerous tags
    config = yaml.load(raw_yaml, Loader=yaml.FullLoader)

    return jsonify({'parsed': str(config)})


# =====================================================================
# MIDDLEWARE / ERROR HANDLERS
# =====================================================================

@app.before_request
def log_request():
    """
    MAJOR — CWE-532: Sensitive Data in Logs

    Logs full request body including passwords, card numbers, tokens.
    """
    logging.debug(f"REQUEST {request.method} {request.path} body={request.get_data(as_text=True)}")
    logging.debug(f"Headers: {dict(request.headers)}")  # VULNERABLE: logs auth headers


@app.after_request
def add_headers(response):
    """
    MAJOR — CWE-693: Missing Security Headers

    No CSP, no X-Frame-Options, no HSTS, no X-Content-Type-Options.
    """
    # VULNERABLE: CORS wildcard
    response.headers['Access-Control-Allow-Origin'] = ALLOWED_ORIGINS
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'  # VULNERABLE with wildcard origin

    # VULNERABLE: all protective headers are MISSING
    # Should have: Content-Security-Policy, X-Frame-Options, Strict-Transport-Security,
    #              X-Content-Type-Options, Referrer-Policy, Permissions-Policy

    return response


@app.errorhandler(500)
def internal_error(error):
    """
    MAJOR — CWE-209: Error Info Disclosure

    Returns full traceback and environment to the client.
    """
    import traceback

    return jsonify({
        'error': str(error),
        'traceback': traceback.format_exc(),
        'environment': {k: v for k, v in os.environ.items()},
        'config': {k: str(v) for k, v in app.config.items()}
    }), 500


# =====================================================================
# BACKGROUND JOBS (simulated)
# =====================================================================

def nightly_report_job():
    """
    MAJOR — CWE-377: Insecure Temp File
    MAJOR — CWE-732: Incorrect Permission Assignment
    """
    report_path = f"/tmp/nightly_report_{datetime.now().strftime('%Y%m%d')}.csv"

    db = sqlite3.connect('/var/data/payments.db')

    # VULNERABLE: SELECT * includes card numbers, CVVs
    rows = db.execute("SELECT * FROM payments WHERE status = 'completed'").fetchall()

    # VULNERABLE: world-readable temp file with PII
    with open(report_path, 'w') as f:
        for row in rows:
            f.write(','.join(str(col) for col in row) + '\n')

    # VULNERABLE: file persists in /tmp indefinitely
    os.chmod(report_path, 0o777)  # world-readable + writable + executable

    logging.info(f"Nightly report written to {report_path}")


def purge_old_data():
    """
    CRITICAL — CWE-78: Command Injection in Scheduled Job

    Cron-like job that builds a shell command from a config value.
    """
    # Imagine retention_days comes from a YAML config an attacker can edit
    retention_days = os.environ.get('RETENTION_DAYS', '90')

    # VULNERABLE: unsanitized env var in shell command
    os.system(f"find /var/data/archives -mtime +{retention_days} -delete")


# =====================================================================
# STARTUP
# =====================================================================

if __name__ == '__main__':
    # CRITICAL — CWE-668: Binding to all interfaces in production
    # CRITICAL — CWE-489: Debug mode active
    app.run(
        host='0.0.0.0',  # VULNERABLE: listens on all interfaces
        port=8080,
        debug=True,       # VULNERABLE: Werkzeug debugger exposed
        use_reloader=True
    )
