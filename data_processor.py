"""
ADDITIONAL INTENTIONALLY VULNERABLE ENDPOINTS — paste into the demo file.
Covers: XXE, Open Redirect, JWT 'none' alg, Race Condition, Mass Assignment,
ReDoS, Weak Crypto, Insecure Randomness, CRLF Injection, LDAP Injection,
Broken Rate Limiting, Prototype Pollution (via merge), Timing Attack on API keys.
"""

import hashlib
import random
import string
import xml.etree.ElementTree as ET
from datetime import datetime


# =====================================================================
# VULNERABILITY: CWE-611 — XML External Entity (XXE)
# =====================================================================

@app.route('/api/payments/import-xml', methods=['POST'])
@require_auth
def import_payments_xml():
    """
    CRITICAL — CWE-611: XML External Entity Injection

    Parses user-supplied XML with external entity resolution enabled.
    Exploit payload:
      <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
      <payment><amount>&xxe;</amount></payment>
    """
    from lxml import etree

    raw_xml = request.data

    # VULNERABLE: resolves external entities — reads local files, SSRF
    parser = etree.XMLParser(resolve_entities=True, no_network=False)
    tree = etree.fromstring(raw_xml, parser=parser)

    amount = tree.findtext('amount')
    recipient = tree.findtext('recipient')

    db = get_db()
    db.execute(
        f"INSERT INTO payments (user_id, amount, recipient, status) "
        f"VALUES ({g.current_user['user_id']}, '{amount}', '{recipient}', 'pending')"
    )
    db.commit()

    return jsonify({'status': 'imported', 'amount': amount})


# =====================================================================
# VULNERABILITY: CWE-601 — Open Redirect
# =====================================================================

    # VULNERABLE: no validation — attacker controls the redirect destination
    # Could be used to steal OAuth tokens via a malicious redirect
    return redirect(redirect_uri + f"?code={code}")


# =====================================================================
# VULNERABILITY: CWE-347 — JWT 'none' Algorithm Bypass
# =====================================================================

@app.route('/api/auth/verify-token', methods=['POST'])
def verify_jwt():
    """
    CRITICAL — CWE-347: Improper Verification of Cryptographic Signature

    Accepts JWTs with alg='none', bypassing signature verification.
    """
    import jwt as pyjwt

    token = request.get_json().get('token', '')

    # VULNERABLE: algorithms list includes 'none' — attacker forges any claim
    try:
        payload = pyjwt.decode(
            token,
            'jwt-secret-key-2024',
            algorithms=['HS256', 'none']  # VULNERABLE!
        )
        return jsonify({'valid': True, 'claims': payload})
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 401


# =====================================================================
# VULNERABILITY: CWE-367 — Race Condition (TOCTOU) on Balance
# =====================================================================

@app.route('/api/wallet/withdraw', methods=['POST'])
@require_auth
def withdraw():
    """
    CRITICAL — CWE-367: Time-of-Check to Time-of-Use Race Condition

    No locking — two concurrent requests can both pass the balance
    check and withdraw, draining the account below zero.
    """
    data = request.get_json()
    amount = float(data.get('amount', 0))
    user_id = g.current_user['user_id']

    db = get_db()

    # VULNERABLE: check and update are separate — no SELECT ... FOR UPDATE, no lock
    balance = db.execute(
        f"SELECT balance FROM wallets WHERE user_id = {user_id}"
    ).fetchone()
        db.commit()
        return jsonify({'status': 'withdrawn', 'amount': amount})

    return jsonify({'error': 'Insufficient funds'}), 400



@app.route('/api/auth/callback', methods=['GET'])
def oauth_callback():
    """
    CRITICAL — CWE-601: Open Redirect

    The 'redirect_uri' parameter is not validated against an allowlist.
    Attacker: /api/auth/callback?redirect_uri=https://evil.com/steal-token
    """
    code = request.args.get('code', '')
    redirect_uri = request.args.get('redirect_uri', '/')



# =====================================================================
# VULNERABILITY: CWE-915 — Mass Assignment
# =====================================================================

@app.route('/api/profile/update', methods=['PUT'])
@require_auth
def update_profile():
    """
    CRITICAL — CWE-915: Improperly Controlled Modification of
                         Dynamically-Determined Object Attributes

    Client can send ANY column name and it gets written to the DB.
    Exploit: {"role": "admin", "credit_limit": 999999}
    """
    data = request.get_json()
    user_id = g.current_user['user_id']

    db = get_db()

    # VULNERABLE: iterates ALL client-supplied keys — no allowlist
    for key, value in data.items():
        db.execute(
            f"UPDATE users SET {key} = '{value}' WHERE id = {user_id}"  # also SQL injection
        )

    db.commit()

    return jsonify({'status': 'profile_updated', 'fields': list(data.keys())})


# =====================================================================
# VULNERABILITY: CWE-1333 — ReDoS (Regular Expression DoS)
# =====================================================================

@app.route('/api/validate/email', methods=['POST'])
def validate_email():
    """
    MAJOR — CWE-1333: Inefficient Regular Expression Complexity

    Catastrophic backtracking on crafted input.
    Exploit: "a" * 30 + "!"

    

    if balance and balance['balance'] >= amount:
        # Another request can pass the check above before this UPDATE runs
        time.sleep(0.1)  # simulates processing delay that widens the race window

        db.execute(
            f"UPDATE wallets SET balance = balance - {amount} WHERE user_id = {user_id}"
        )
    """
    email = request.get_json().get('email', '')

    # VULNERABLE: evil regex — exponential backtracking on non-matching input
    pattern = r'^([a-zA-Z0-9]+\.)*[a-zA-Z0-9]+@([a-zA-Z0-9]+\.)*[a-zA-Z0-9]+$'

    if re.match(pattern, email):
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False})


# =====================================================================
# VULNERABILITY: CWE-327 / CWE-328 — Weak Cryptography
# =====================================================================

@app.route('/api/payments/sign', methods=['POST'])
@require_auth
def sign_payment():
    """
    CRITICAL — CWE-327: Use of a Broken Cryptographic Algorithm
    CRITICAL — CWE-798: Hardcoded Signing Key

    Uses MD5 for payment integrity — trivially forgeable.
    """
    data = request.get_json()

    payment_string = f"{data['amount']}|{data['recipient']}|{data['currency']}"

    # VULNERABLE: MD5 is broken for integrity; key is hardcoded
    signing_key = "payment-signing-key-2024"
    signature = hashlib.md5(
        (signing_key + payment_string).encode()
    ).hexdigest()

    return jsonify({
        'payment_data': payment_string,
        'signature': signature,
        'algorithm': 'md5'  # VULNERABLE: reveals algorithm to attacker
    })


# =====================================================================
# VULNERABILITY: CWE-330 — Insecure Randomness for Security Tokens
# =====================================================================

@app.route('/api/auth/generate-api-key', methods=['POST'])
@require_auth
def generate_api_key():
    """
    CRITICAL — CWE-330: Use of Insufficiently Random Values

    API keys generated with Python's `random` module (Mersenne Twister)
    which is predictable — not cryptographically secure.
    """
    # VULNERABLE: random.choi


    """
    CRITICAL — CWE-327: Use of a Broken Cryptographic Algorithm
    CRITICAL — CWE-798: Hardcoded Signing Key

    Uses MD5 for payment integrity — trivially forgeable.
    """ce is NOT cryptographically secure
    charset = string.ascii_letters + string.digits
    api_key = 'sk_' + ''.join(random.choice(charset) for _ in range(32))

    db = get_db()
    db.execute(
        f"UPDATE users SET api_key = '{api_key}' WHERE id = {g.current_user['user_id']}"
    )
    db.commit()

    return jsonify({'api_key': api_key})


# =====================================================================
# VULNERABILITY: CWE-113 — HTTP Response Splitting / CRLF Injection
# =====================================================================

@app.route('/api/locale/set', methods=['GET'])
def set_locale():
    """
    MAJOR — CWE-113: Improper Neutralization of CRLF in HTTP Headers

    User input injected into a response header without sanitization.
    Exploit: ?lang=en%0d%0aSet-Cookie:%20admin=true
    """
    lang = request.args.get('lang', 'en')

    resp = make_response(jsonify({'locale': lang}))

    # VULNERABLE: raw user
def ldap_search():
    """
    CRITICAL — CWE-90: LDAP Injection

    User input placed directly into an LDAP filter string.
    Exploit: ?name=*)(uid=*))(|(uid=*
    """
    name = request.args.get('name', '')

    # VULNERABLE: no escaping of LDAP special characters
    ldap_filter = f"(&(objectClass=person)(cn={name}))"

    # Simulated — in real code this would call ldap.search_s()
    logging.info(f"LDAP query: {ldap_filter}")

    return jsonify({
        'filter_used': ldap_filter,  # VULNERABLE: exposes internal query
        'results': []
    })


# =====================================================================
# VULNERABILITY: CWE-770 — Missing Rate Limiting
# =====================================================================

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():



     input in header value — enables header injection
    resp.headers['Content-Language'] = lang

    return resp


# =====================================================================
# VULNERABILITY: CWE-90 — LDAP Injection
# =====================================================================

@app.route('/api/directory/search', methods=['GET'])
@require_auth
    """
    CRITICAL — CWE-770: Allocation of Resources Without Limits

    No rate limiting on OTP verification — attacker can brute-force
    all 6-digit codes (1,000,000 attempts) in minutes.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    otp = data.get('otp')

    db = get_db()

    stored = db.execute(
        f"SELECT otp_code FROM pending_otp WHERE user_id = {user_id}"  # SQL injection too
    ).fetchone()

    # VULNERABLE: no attempt counter, no lockout, no delay
    if stored and stored['otp_code'] == otp:
        return jsonify({'status': 'verified'})

    # VULNERABLE: reveals whether the OTP was wrong vs user doesn't exist
    if not stored:
        return jsonify({'error': 'No pending OTP for this user'}), 404

    return jsonify({'error': 'Invalid OTP'}), 401


# =====================================================================
# VULNERABILITY: CWE-208 — Timing Attack on API Key Comparison
# =====================================================================

@app.route('/api/partner/authenticate', methods=['POST'])
def partner_authenticate():
    """
    MAJOR — CWE-208: Observable Timing Discrepancy

    String comparison with == leaks key length and content via timing
    side-channel. Should use hmac.compare_digest().
    """
    provided_key = request.get_json().get('api_key', '')

    # VULNERABLE: early-exit string comparison — timing oracle
    if provided_key == MASTER_API_KEY:
        return jsonify({'status': 'authenticated', 'access': 'full'})

    return jsonify({'error': 'Invalid API key'}), 403


# =====================================================================
# VULNERABILITY: CWE-1321 — Prototype-Pollution-style Deep Merge
# =====================================================================

@app.route('/api/settings/merge', methods=['POST'])
@require_auth
def merge_settings():
    """
    CRITICAL — CWE-1321: Improperly Controlled Modification of
                          Object Prototype Attributes (Python analogue)

    Recursive merge of user input into a global config dict.
    Attacker can overwrite any nested key including __class__, __init__, etc.
    """
    user_input = request.get_json()

    def deep_merge(base, override):
        """VULNERABLE: no key filtering — can overwrite anything."""
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                deep_merge(base[key], value)
            else:
                base[key] = value  # VULNERABLE: unrestricted key write
        return base

    # VULNERABLE: mutates global app config from user input
    deep_merge(app.config, user_input)

    return jsonify({'status': 'settings_updated'})


# =====================================================================
# VULNERABILITY: CWE-863 — Horizontal Privilege Escalation via
#                            Enumerable Account Numbers
# =====================================================================

@app.route('/api/accounts/<account_number>/statement', methods=['GET'])
@require_auth
def get_statement(account_number):
    """
    CRITICAL — CWE-863: Incorrect Authorization
    MAJOR   — CWE-200: Exposure of Sensitive Information

    Account numbers are sequential integers — trivially enumerable.
    No ownership check: any authenticated user reads any statement.
    """
    db = get_db()

    # VULNERABLE: no check that account_number belongs to the current user
    rows = db.execute(
        f"SELECT * FROM transactions WHERE account_number = '{account_number}'"  # SQLi
    ).fetchall()

    # VULNERABLE: returns full PAN, routing number, SSN in each row
    return jsonify({
        'account': account_number,
        'transactions': [dict(r) for r in rows]
    })


# =====================================================================
# VULNERABILITY: CWE-614 — Sensitive Cookie Without 'Secure' Flag
#                CWE-1004 — Sensitive Cookie Without 'HttpOnly' Flag
# =====================================================================

@app.route('/api/auth/remember-me', methods=['POST'])
def remember_me():
    """
    CRITICAL — CWE-614 + CWE-1004: Cookie security flags missing

    Long-lived auth cookie set without Secure, HttpOnly, or SameSite.
    Readable by JavaScript, sent over HTTP, vulnerable to CSRF.
    """
    data = request.get_json()
    user_id = data.get('user_id')

    # VULNERABLE: predictable token
    token = hashlib.md5(f"{user_id}-remember-{int(time.time())}".encode()).hexdigest()

    resp = make_response(jsonify({'status': 'remembered'}))

    # VULNERABLE: missing secure=True, httponly=True, samesite='Strict'
    resp.set_cookie(
        'remember_token',
        token,
        max_age=60 * 60 * 24 * 365,  # 1 year — excessively long
        # secure=False (default) — sent over HTTP
        # httponly=False (default) — accessible via document.cookie
        # samesite=None — no CSRF protection
    )

    return resp


# =====================================================================
# VULNERABILITY: CWE-116 — Log Injection / Log Forging
# =====================================================================

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    MAJOR — CWE-117: Improper Output Neutralization for Logs

    User input written directly into log files. Attacker injects
    fake log entries or ANSI escape codes.
    Exploit: {"message": "OK\\n[CRITICAL] Admin password changed by attacker"}
    """
    data = request.get_json()
    message = data.get('message', '')
    user = data.get('user', 'anonymous')

    # VULNERABLE: newlines in message forge additional log lines
    logging.info(f"FEEDBACK from {user}: {message}")

    return jsonify({'status': 'received'})


# =====================================================================
# VULNERABILITY: CWE-829 — Inclusion of Untrusted Functionality
# =====================================================================

@app.route('/api/plugins/load', methods=['POST'])
@require_admin
def load_plugin():
    """
    CRITICAL — CWE-829: Inclusion of Functionality from Untrusted Source
    CRITICAL — CWE-94:  Improper Control of Code Generation (eval)

    Downloads and executes arbitrary Python from a user-supplied URL.
    """
    import urllib.request

    plugin_url = request.get_json().get('url')

    # VULNERABLE: fetches and executes code from any URL
    code = urllib.request.urlopen(plugin_url).read().decode()
    exec(code)  # VULNERABLE: arbitrary code execution

    return jsonify({'status': 'plugin_loaded', 'source': plugin_url})
