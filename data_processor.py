#!/usr/bin/env python3
"""
Payment Data Processor - INTENTIONALLY VULNERABLE FOR DEMO

Vulnerabilities:
1. Command Injection
2. SQL Injection
3. Path Traversal
4. Hardcoded Credentials
5. Insecure Deserialization
6. XXE (XML External Entity)
7. Unsafe YAML loading
8. Weak Crypto (MD5)
9. Disabled SSL
10. SSRF
11. Log Injection
12. Race Condition
13. NoSQL Injection
14. Insufficient Input Validation
--- NEW CRITICAL / MAJOR ---
15. JWT None Algorithm
16. Insecure Temp File
17. Arbitrary Code Execution via exec()
18. Mass Assignment / Object Injection
19. Cleartext Password Storage
20. Unvalidated Redirect
21. Buffer-style ReDoS
22. Improper Access Control
23. Sensitive Data in URL
24. Weak Random for Tokens
25. Debug Mode / Stack Trace Exposure
26. Prototype Pollution via merge
27. Unrestricted File Upload
28. Integer Overflow in Payment Amount
29. Missing Rate Limiting on Auth
30. Hardcoded Encryption Key + ECB Mode
"""

import os
import sys
import subprocess
import mysql.connector
import pickle
import yaml
import xml.etree.ElementTree as ET
import hashlib
import json
import random
import string
import tempfile
import re

# ============================================
# VULNERABILITY 1: Hardcoded Database Credentials
# CWE-798
# ============================================
DB_HOST = "prod-db.bank.internal"
DB_USER = "admin"
DB_PASSWORD = "Pr0dP@ssw0rd123!"  # VULNERABLE!
DB_NAME = "payments_db"

# VULNERABILITY 2: Hardcoded API Keys
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"  # VULNERABLE!
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # VULNERABLE!

# VULNERABILITY (NEW): Hardcoded JWT Secret + Encryption Key
JWT_SECRET = "super-secret-jwt-key-12345"  # VULNERABLE!
ENCRYPTION_KEY = b"0123456789ABCDEF"  # VULNERABLE! Hardcoded 128-bit key

# VULNERABILITY (NEW): Debug mode enabled in production
DEBUG_MODE = True  # VULNERABLE! Exposes stack traces and internal state


def process_payment_file(filename):
    """
    VULNERABILITY 3: Command Injection
    CWE-78
    User input directly used in shell command
    """
    # VULNERABLE: User-controlled filename in shell command
    command = f"cat /data/payments/{filename} | wc -l"

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Processed {result.stdout.strip()} records")
        return result.stdout
    except Exception as e:
        print(f"Error: {e}")
        return None


def export_payments_to_csv(output_file, query_filter):
    """
    VULNERABILITY 4: SQL Injection
    CWE-89
    Direct string concatenation in SQL query
    """
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        # VULNERABLE: SQL Injection via string concatenation
        sql = f"SELECT * FROM payments WHERE {query_filter}"

        print(f"Executing SQL: {sql}")  # VULNERABLE: Logging SQL queries

        cursor.execute(sql)
        results = cursor.fetchall()

        # VULNERABILITY 5: Path Traversal
        with open(output_file, 'w') as f:
            for row in results:
                f.write(','.join(str(col) for col in row) + '\n')

        cursor.close()
        conn.close()

        print(f"Exported {len(results)} payments to {output_file}")

    except Exception as e:
        # VULNERABILITY 6: Error Information Disclosure
        print(f"Database error: {str(e)}")
        import traceback
        traceback.print_exc()


def generate_report(report_type, parameters):
    """
    VULNERABILITY 7: Command Injection via system()
    CWE-78
    """
    if report_type == "daily":
        cmd = f"python3 /opt/reports/daily_report.py {parameters}"
    elif report_type == "monthly":
        cmd = f"python3 /opt/reports/monthly_report.py {parameters}"
    else:
        cmd = f"python3 /opt/reports/custom_report.py {parameters}"

    os.system(cmd)


def load_configuration(config_file):
    """
    VULNERABILITY 8: Insecure Deserialization
    CWE-502
    """
    with open(config_file, 'rb') as f:
        config = pickle.load(f)  # DANGEROUS!

    return config


def load_yaml_config(yaml_file):
    """
    VULNERABILITY 10: Unsafe YAML Deserialization
    CWE-502
    """
    with open(yaml_file, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)  # Still vulnerable

    return config


def execute_data_migration(source_db, migration_script):
    """
    VULNERABILITY 11: OS Command Injection with eval()
    CWE-95
    """
    migration_params = {
        'source': source_db,
        'target': DB_NAME,
        'credentials': {'user': DB_USER, 'password': DB_PASSWORD}
    }

    result = eval(f"execute_migration({migration_params}, '{migration_script}')")

    return result


def backup_to_s3(bucket_name, file_path):
    """
    VULNERABILITY 12: Hardcoded AWS Credentials + Command Injection
    """
    os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY
    os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_KEY

    command = f"aws s3 cp {file_path} s3://{bucket_name}/"
    os.system(command)


def search_payments(search_term):
    """
    VULNERABILITY 13: NoSQL Injection (MongoDB)
    """
    from pymongo import MongoClient

    client = MongoClient('mongodb://admin:M0ng0P@ss!@prod-mongo.bank.internal:27017/')
    db = client['payments']

    results = db.payments.find({'description': search_term})

    return list(results)


def sanitize_filename(filename):
    """
    VULNERABILITY 14: Insufficient Input Validation
    """
    cleaned = filename.replace('../', '')
    return cleaned


def download_payment_receipt(receipt_url):
    """
    VULNERABILITY 15: Server-Side Request Forgery (SSRF)
    CWE-918
    """
    import urllib.request

    try:
        response = urllib.request.urlopen(receipt_url)
        data = response.read()
        return data
    except Exception as e:
        print(f"Download error: {e}")
        return None


def process_payment_batch(batch_file):
    """
    VULNERABILITY 16: Race Condition (TOCTOU)
    """
    if os.path.exists(batch_file):
        with open(batch_file, 'r') as f:
            data = f.read()
        process_data(data)


def log_payment_transaction(transaction_data):
    """
    VULNERABILITY 17: Log Injection
    CWE-117
    """
    print(f"[INFO] Payment processed by user: {transaction_data['user']}")
    print(f"[INFO] Amount: {transaction_data['amount']}")
    print(f"[INFO] Account: {transaction_data['account']}")


def parse_payment_xml(xml_file):
    """
    VULNERABILITY 9: XML External Entity (XXE) Attack
    CWE-611
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    payments = []
    for payment in root.findall('payment'):
        payments.append({
            'id': payment.find('id').text,
            'amount': payment.find('amount').text,
            'account': payment.find('account').text
        })
    return payments


def calculate_payment_hash(payment_data):
    """
    VULNERABILITY 18: Weak Cryptographic Hash (MD5)
    CWE-327
    """
    payment_string = f"{payment_data['id']}{payment_data['amount']}{payment_data['account']}"
    hash_value = hashlib.md5(payment_string.encode()).hexdigest()

    return hash_value


def connect_to_payment_api(endpoint):
    """
    VULNERABILITY 19: Disabled SSL Verification
    CWE-295
    """
    import requests

    response = requests.get(
        f"https://api.bank.com/{endpoint}",
        verify=False  # DANGEROUS!
    )
    return response.json()


# =====================================================================
# NEW CRITICAL & MAJOR VULNERABILITIES
# =====================================================================


def generate_auth_token(user_id):
    """
    CRITICAL — VULNERABILITY 21: JWT None-Algorithm Attack
    CWE-345 (Insufficient Verification of Data Authenticity)

    Accepts the 'none' algorithm, allowing an attacker to forge tokens
    with no signature at all.
    """
    import jwt

    payload = {
        'user_id': user_id,
        'role': 'user',
        'exp': 9999999999
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token


def verify_auth_token(token):
    """
    CRITICAL — Accepts 'none' algorithm, so forged unsigned tokens pass validation.
    """
    import jwt

    # VULNERABLE: allows algorithm override from token header — attacker sets alg=none
    decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256', 'none'])
    return decoded


def store_user_credentials(username, password):
    """
    CRITICAL — VULNERABILITY 22: Cleartext Password Storage
    CWE-256

    Passwords stored in plaintext in the database.
    """
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    cursor = conn.cursor()

    # VULNERABLE: storing password as plaintext — no hashing at all
    sql = f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"
    cursor.execute(sql)  # Also SQL injection via username/password

    conn.commit()
    cursor.close()
    conn.close()


def generate_session_token():
    """
    CRITICAL — VULNERABILITY 23: Weak Randomness for Security Tokens
    CWE-330

    Uses Python's `random` module (Mersenne Twister, not cryptographically secure)
    to generate session tokens. Predictable.
    """
    # VULNERABLE: random module is NOT cryptographically secure
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    return token


def generate_password_reset_link(user_email):
    """
    CRITICAL — VULNERABILITY 24: Sensitive Data in URL / GET Parameters
    CWE-598

    Password-reset token placed in a GET URL that will appear in server
    logs, browser history, Referer headers, and proxy caches.
    """
    import time

    # VULNERABLE: predictable token (timestamp-based)
    reset_token = hashlib.md5(f"{user_email}{time.time()}".encode()).hexdigest()

    # VULNERABLE: sensitive token in URL query string
    reset_link = f"https://bank.com/reset-password?email={user_email}&token={reset_token}"

    print(f"Password reset link: {reset_link}")  # VULNERABLE: logging PII + token
    return reset_link


def upload_payment_proof(file_obj, filename):
    """
    CRITICAL — VULNERABILITY 25: Unrestricted File Upload
    CWE-434

    No validation of file type, size, or content.
    Attacker can upload a web shell (.php, .jsp, .py).
    """
    # VULNERABLE: no file-type validation, no size limit, no content inspection
    upload_dir = "/var/www/uploads/"

    # VULNERABLE: using user-supplied filename directly (path traversal + overwrite)
    dest_path = os.path.join(upload_dir, filename)

    with open(dest_path, 'wb') as f:
        f.write(file_obj.read())

    # VULNERABLE: returning a publicly accessible URL to the uploaded file
    return f"https://bank.com/uploads/{filename}"


def authenticate_user(username, password):
    """
    CRITICAL — VULNERABILITY 26: Missing Rate Limiting / Brute-Force Protection
    CWE-307

    No lockout, no delay, no CAPTCHA — unlimited login attempts.
    """
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    cursor = conn.cursor()

    # VULNERABLE: SQL injection AND no rate limiting
    sql = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(sql)

    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        # VULNERABLE: session token via weak random
        return {'authenticated': True, 'session': generate_session_token()}
    else:
        # VULNERABLE: user enumeration — different messages for bad user vs bad password
        return {'authenticated': False, 'error': 'Invalid password for this account'}


def encrypt_payment_data(plaintext):
    """
    CRITICAL — VULNERABILITY 27: Hardcoded Key + ECB Mode
    CWE-327 / CWE-798

    AES-ECB leaks data patterns; the key is hardcoded in source.
    """
    from Crypto.Cipher import AES

    # VULNERABLE: ECB mode leaks patterns in ciphertext
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_ECB)

    # VULNERABLE: naive PKCS-style padding
    padded = plaintext.encode().ljust((len(plaintext) // 16 + 1) * 16, b'\0')
    encrypted = cipher.encrypt(padded)

    return encrypted


def process_webhook_payload(raw_body):
    """
    CRITICAL — VULNERABILITY 28: Arbitrary Code Execution via exec()
    CWE-94

    Runs user-supplied code from a webhook body.
    """
    payload = json.loads(raw_body)

    # VULNERABLE: exec() on user-controlled string
    if 'transform' in payload:
        exec(payload['transform'])  # Attacker sends arbitrary Python

    return payload.get('data', {})


def update_user_profile(user_id, update_data):
    """
    MAJOR — VULNERABILITY 29: Mass Assignment / Object Injection
    CWE-915

    Accepts arbitrary fields from client — attacker can set
    `role`, `is_admin`, `balance`, etc.
    """
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    cursor = conn.cursor()

    # VULNERABLE: blindly iterates over all user-supplied keys
    for key, value in update_data.items():
        sql = f"UPDATE users SET {key} = '{value}' WHERE id = {user_id}"
        cursor.execute(sql)

    conn.commit()
    cursor.close()
    conn.close()


def redirect_after_payment(return_url):
    """
    MAJOR — VULNERABILITY 30: Unvalidated Redirect
    CWE-601

    Attacker controls the redirect target — enables phishing.
    """
    from flask import redirect

    # VULNERABLE: no allowlist check on return_url
    # Exploit: return_url = "https://evil-bank.com/steal-creds"
    return redirect(return_url)


def validate_transaction_reference(ref):
    """
    MAJOR — VULNERABILITY 31: ReDoS (Regular Expression Denial of Service)
    CWE-1333

    Catastrophic backtracking on crafted input.
    """
    # VULNERABLE: nested quantifiers cause exponential backtracking
    pattern = r'^([a-zA-Z0-9]+)+\-[a-zA-Z0-9]+$'

    if re.match(pattern, ref):
        return True
    return False


def get_payment_details(payment_id, requesting_user):
    """
    MAJOR — VULNERABILITY 32: Broken Access Control / IDOR
    CWE-639

    Any authenticated user can view any payment — no ownership check.
    """
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    cursor = conn.cursor()

    # VULNERABLE: no check that requesting_user owns this payment_id
    sql = f"SELECT * FROM payments WHERE id = {payment_id}"
    cursor.execute(sql)

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result


def create_temp_payment_file(data):
    """
    MAJOR — VULNERABILITY 33: Insecure Temp File Creation
    CWE-377

    Predictable filename in world-readable /tmp — symlink attacks possible.
    """
    # VULNERABLE: predictable filename, default permissions
    tmp_path = f"/tmp/payment_{os.getpid()}.json"

    with open(tmp_path, 'w') as f:
        json.dump(data, f)  # may contain PII, card numbers, etc.

    return tmp_path


def deep_merge(base, overrides):
    """
    MAJOR — VULNERABILITY 34: Prototype Pollution via Recursive Merge
    CWE-1321

    Attacker-controlled keys like __class__, __init__, __globals__
    can poison internal object state.
    """
    for key, value in overrides.items():
        # VULNERABLE: no key filtering — allows dunder / prototype keys
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def error_handler(request_data):
    """
    MAJOR — VULNERABILITY 35: Debug / Stack Trace Exposure in Production
    CWE-209 / CWE-215
    """
    try:
        result = process_complex_payment(request_data)
        return result
    except Exception as e:
        if DEBUG_MODE:
            import traceback
            # VULNERABLE: full stack trace + local variable dump returned to client
            error_detail = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'request_data': request_data,  # echoes back PII
                'db_host': DB_HOST,
                'db_user': DB_USER,
                'db_password': DB_PASSWORD,  # leaks credentials in error response!
                'environment': dict(os.environ)  # leaks ALL env vars
            }
            return error_detail


def validate_payment_amount(amount_str):
    """
    MAJOR — VULNERABILITY 36: Integer Overflow in Payment Amount
    CWE-190

    No upper-bound validation — attacker can overflow or cause
    negative-wrap amounts.
    """
    # VULNERABLE: no bounds check, no type enforcement
    amount = int(amount_str)

    # Negative amounts could trigger refunds to attacker
    if amount == 0:
        raise ValueError("Amount cannot be zero")

    # No upper-bound — 99999999999999 could overflow downstream int32 fields
    return amount


def fetch_user_payments(user_id):
    """
    MAJOR — VULNERABILITY 37: GraphQL-style Over-fetching / Info Disclosure
    Returns all columns including PII to any caller.
    """
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    cursor = conn.cursor(dictionary=True)

    # VULNERABLE: SELECT * exposes SSN, full card number, CVV, etc.
    cursor.execute(f"SELECT * FROM payments WHERE user_id = {user_id}")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # VULNERABLE: dumps all fields to client — no field filtering
    return json.dumps(rows)


# =====================================================================
# MAIN
# =====================================================================

def main():
    """
    Main function with multiple vulnerabilities
    """
    if len(sys.argv) < 2:
        print("Usage: python data_processor.py <command> [args]")
        sys.exit(1)

    command = sys.argv[1]

    # VULNERABILITY 20: Unrestricted Command Execution
    if command == "process":
        filename = sys.argv[2] if len(sys.argv) > 2 else "default.csv"
        process_payment_file(filename)

    elif command == "export":
        output = sys.argv[2] if len(sys.argv) > 2 else "export.csv"
        query = sys.argv[3] if len(sys.argv) > 3 else "status='PENDING'"
        export_payments_to_csv(output, query)

    elif command == "report":
        report_type = sys.argv[2] if len(sys.argv) > 2 else "daily"
        params = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        generate_report(report_type, params)

    elif command == "backup":
        bucket = sys.argv[2] if len(sys.argv) > 2 else "bank-backups"
        file_path = sys.argv[3] if len(sys.argv) > 3 else "/data/backup.sql"
        backup_to_s3(bucket, file_path)

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()


# =====================================================================
# SECURE REFERENCE IMPLEMENTATIONS (for comparison)
# =====================================================================

def secure_command_execution(filename):
    """SECURE: Using parameterized command execution"""
    import shlex

    if not filename.endswith('.csv'):
        raise ValueError("Invalid file type")

    result = subprocess.run(
        ['wc', '-l', f'/data/payments/{filename}'],
        capture_output=True,
        text=True
    )
    return result.stdout


def secure_sql_query(query_filter):
    """SECURE: Using parameterized queries"""
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME')
    )
    cursor = conn.cursor()

    sql = "SELECT * FROM payments WHERE status = %s AND amount > %s"
    cursor.execute(sql, (query_filter['status'], query_filter['amount']))

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def secure_file_write(output_file, data):
    """SECURE: Validate path and use safe directory"""
    import pathlib

    safe_dir = pathlib.Path('/var/exports/')
    output_path = (safe_dir / output_file).resolve()

    if not str(output_path).startswith(str(safe_dir)):
        raise ValueError("Invalid output path")

    with open(output_path, 'w') as f:
        f.write(data)
