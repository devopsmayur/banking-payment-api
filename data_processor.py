"""
ADDITIONAL DEMO ENDPOINTS — PART 2
Covers categories underrepresented in part 1: Performance & Scalability,
Stability & Availability, Functional Correctness, Data Integrity &
Integration, and Maintainability & Code Quality.

These are intentionally flawed, for exercising automated code review
(e.g. CodeRabbit) against a broad rule set. Do not deploy.
"""

import json
import os
import threading
import requests  # NOTE: add to requirements if not already present


# =====================================================================
# PERFORMANCE: N+1 Query Pattern
# =====================================================================

@app.route('/api/orders/list-with-items', methods=['GET'])
@require_auth
def list_orders_with_items():
    """
    PERFORMANCE — N+1 Query Problem

    Fetches all orders, then issues one additional query PER order to
    fetch its line items, instead of a single JOIN or batched IN query.
    With 1,000 orders this is 1,001 round trips to the DB.
    """
    db = get_db()
    orders = db.execute(
        f"SELECT * FROM orders WHERE user_id = {g.current_user['user_id']}"
    ).fetchall()

    order_ids = [order['id'] for order in orders]
    items_by_order = {}
    if order_ids:
        placeholders = ', '.join('?' for _ in order_ids)
        items = db.execute(
            f"SELECT * FROM order_items WHERE order_id IN ({placeholders})",
            order_ids,
        ).fetchall()
        for item in items:
            items_by_order.setdefault(item['order_id'], []).append(item)

    result = []
    for order in orders:
        items = items_by_order.get(order['id'], [])
        result.append({'order': dict(order), 'items': [dict(i) for i in items]})

    return jsonify(result)


# =====================================================================
# PERFORMANCE: Missing Caching on Expensive/Repeated Computation
# =====================================================================

@app.route('/api/reports/monthly-summary', methods=['GET'])
@require_auth
def monthly_summary():
    """
    PERFORMANCE — Missing Caching

    Recomputes an expensive aggregate on every single request, even
    though the underlying data (last month's closed transactions)
    never changes after month-end. No cache layer, no memoization.
    """
    db = get_db()
    month = request.args.get('month')

    # PERFORMANCE: full table scan + aggregation on every call, no cache
    rows = db.execute(
        f"SELECT * FROM transactions WHERE month = '{month}' AND status = 'closed'"
    ).fetchall()

    total = 0
    by_category = {}
    for r in rows:
        total += r['amount']
        by_category.setdefault(r['category'], 0)
        by_category[r['category']] += r['amount']

    return jsonify({'total': total, 'by_category': by_category})


# =====================================================================
# PERFORMANCE: Unbounded / Unpaginated List Endpoint
# =====================================================================

@app.route('/api/transactions/all', methods=['GET'])
@require_auth
def all_transactions():
    """
    PERFORMANCE — Unbounded Result Set

    No LIMIT/OFFSET or pagination. On an account with millions of
    transactions this loads the entire table into memory and serializes
    it in one response.
    """
    db = get_db()
    rows = db.execute("SELECT * FROM transactions").fetchall()  # no LIMIT
    return jsonify([dict(r) for r in rows])


# =====================================================================
# STABILITY: Unbounded In-Memory Cache (Memory Leak)
# =====================================================================

_SESSION_CACHE = {}  # module-level dict, never evicted or size-capped


@app.route('/api/session/touch', methods=['POST'])
@require_auth
def touch_session():
    """
    STABILITY — Memory Leak via Unbounded Cache Growth

    Every call adds an entry to a process-global dict that is never
    cleaned up or size-limited. Over the process lifetime this grows
    without bound and will eventually exhaust available memory.
    """
    session_id = request.get_json().get('session_id')

    # STABILITY: no eviction policy, no max size, no TTL
    _SESSION_CACHE[session_id] = {
        'user_id': g.current_user['user_id'],
        'last_seen': datetime.utcnow(),
        'payload': request.get_json(),  # also retains full request body forever
    }

    return jsonify({'status': 'ok', 'cache_size': len(_SESSION_CACHE)})


# =====================================================================
# STABILITY: Unhandled Exception on External Call (No Timeout, No Catch)
# =====================================================================

@app.route('/api/shipping/rate-quote', methods=['POST'])
@require_auth
def rate_quote():
    """
    STABILITY — Unhandled Exception / No Timeout

    Calls an external carrier API with no timeout and no exception
    handling. A slow or unreachable upstream service will hang the
    worker thread indefinitely and an HTTP error or malformed JSON
    response will crash this request with an unhandled exception.
    """
    data = request.get_json()

    # STABILITY: no timeout= kwarg, no try/except around network I/O
    response = requests.post(
        "https://carrier.example.com/v1/quote",
        json={'weight': data['weight'], 'destination': data['destination']},
    )

    # STABILITY: assumes response is always 200 with this exact shape
    quote = response.json()['quote']['amount']

    return jsonify({'quote': quote})


# =====================================================================
# STABILITY: Deadlock-Prone Lock Ordering
# =====================================================================

_lock_a = threading.Lock()
_lock_b = threading.Lock()


@app.route('/api/transfer/internal', methods=['POST'])
@require_auth
def internal_transfer():
    """
    STABILITY — Inconsistent Lock Ordering (Deadlock Risk)

    Acquires _lock_a then _lock_b. Another code path elsewhere in the
    service (not shown) acquires _lock_b then _lock_a. Under concurrent
    load these two orderings can deadlock the process.
    """
    data = request.get_json()

    with _lock_a:
        with _lock_b:  # STABILITY: opposite acquisition order used elsewhere
            db = get_db()
            db.execute(
                f"UPDATE wallets SET balance = balance - {data['amount']} "
                f"WHERE user_id = {data['from_id']}"
            )
            db.execute(
                f"UPDATE wallets SET balance = balance + {data['amount']} "
                f"WHERE user_id = {data['to_id']}"
            )
            db.commit()

    return jsonify({'status': 'transferred'})


# =====================================================================
# FUNCTIONAL CORRECTNESS: Off-by-One in Pagination
# =====================================================================

@app.route('/api/invoices', methods=['GET'])
@require_auth
def list_invoices():
    """
    FUNCTIONAL CORRECTNESS — Off-by-One Error

    page_size * page is used as the offset for page 1, which skips the
    first page_size records instead of starting at record 0. Page 1
    should have offset 0.
    """
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    # BUG: offset should be (page - 1) * page_size
    offset = page * page_size

    db = get_db()
    rows = db.execute(
        f"SELECT * FROM invoices WHERE user_id = {g.current_user['user_id']} "
        f"LIMIT {page_size} OFFSET {offset}"
    ).fetchall()

    return jsonify([dict(r) for r in rows])


# =====================================================================
# FUNCTIONAL CORRECTNESS: Floating-Point Equality for Currency
# =====================================================================

@app.route('/api/invoices/<invoice_id>/mark-paid', methods=['POST'])
@require_auth
def mark_invoice_paid(invoice_id):
    """
    FUNCTIONAL CORRECTNESS — Floating-Point Equality Comparison

    Compares the paid amount to the invoice total using ==. Floating
    point arithmetic on currency values routinely produces values like
    99.99999999999999, so exact equality silently fails and legitimate
    full payments are left marked unpaid.
    """
    data = request.get_json()
    paid_amount = data['paid_amount']

    db = get_db()
    invoice = db.execute(
        f"SELECT total FROM invoices WHERE id = {invoice_id}"
    ).fetchone()

    # BUG: use a tolerance (e.g. abs(a - b) < 0.01) or integer cents instead
    if paid_amount == invoice['total']:
        db.execute(f"UPDATE invoices SET status = 'paid' WHERE id = {invoice_id}")
        db.commit()
        return jsonify({'status': 'paid'})

    return jsonify({'status': 'partial_or_unpaid'})


# =====================================================================
# FUNCTIONAL CORRECTNESS: Inverted / Wrong Boolean Condition
# =====================================================================

@app.route('/api/users/<user_id>/access', methods=['GET'])
@require_auth
def check_access(user_id):
    """
    FUNCTIONAL CORRECTNESS — Inverted Condition

    The intent is to deny access to suspended accounts, but the
    condition is inverted: it grants access when is_suspended is True
    and denies it otherwise.
    """
    db = get_db()
    user = db.execute(f"SELECT is_suspended FROM users WHERE id = {user_id}").fetchone()

    # BUG: condition is backwards — should be `if not user['is_suspended']`
    if user['is_suspended']:
        return jsonify({'access': 'granted'})

    return jsonify({'access': 'denied'})


# =====================================================================
# DATA INTEGRITY: Missing Transaction / Partial Write on Failure
# =====================================================================

@app.route('/api/orders/create', methods=['POST'])
@require_auth
def create_order():
    """
    DATA INTEGRITY — No Transactional Boundary

    Inserts the order header and its line items as separate,
    non-atomic commits. If the process crashes or an exception is
    raised between the two inserts, the database is left with an
    order that has no items (or items with no parent order).
    """
    data = request.get_json()
    db = get_db()

    db.execute(
        f"INSERT INTO orders (user_id, total) VALUES "
        f"({g.current_user['user_id']}, {data['total']})"
    )
    db.commit()  # DATA INTEGRITY: committed before items are inserted

    order_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    for item in data['items']:
        # If this raises (bad item, connection drop, etc.), the order
        # above is already permanently committed with no items.
        db.execute(
            f"INSERT INTO order_items (order_id, sku, qty) VALUES "
            f"({order_id}, '{item['sku']}', {item['qty']})"
        )
    db.commit()

    return jsonify({'status': 'created', 'order_id': order_id})


# =====================================================================
# DATA INTEGRITY: API Response Schema Drift
# =====================================================================

@app.route('/api/users/<user_id>/profile', methods=['GET'])
@require_auth
def get_profile_v2(user_id):
    """
    DATA INTEGRITY / INTEGRATION — Undocumented Schema Change

    Renames 'created_at' to 'createdAt' and changes 'balance' from a
    numeric type to a formatted string, silently breaking any existing
    client that deserializes this response against the documented v1
    contract (numeric balance, snake_case created_at).
    """
    db = get_db()
    user = db.execute(f"SELECT * FROM users WHERE id = {user_id}").fetchone()

    return jsonify({
        'id': user['id'],
        'createdAt': user['created_at'],          # was created_at (snake_case) in v1
        'balance': f"${user['balance']:.2f}",      # was a raw float in v1
    })


# =====================================================================
# MAINTAINABILITY: Unclear Naming, Magic Numbers, Duplicated Logic
# =====================================================================

@app.route('/api/pricing/calc', methods=['POST'])
@require_auth
def calc():
    """
    MAINTAINABILITY — Poor Naming, Magic Numbers, Copy-Pasted Logic

    Function and variable names give no indication of purpose. Tax and
    discount rates are hardcoded magic numbers instead of named
    constants or config. The discount/tax math is duplicated three
    times with slight copy-paste variations instead of a shared helper.
    """
    d = request.get_json()
    x = d['amt']
    y = d['qty']
    z = x * y

    # MAINTAINABILITY: magic numbers with no explanation
    if d.get('t') == 1:
        z = z - (z * 0.15)
        z = z + (z * 0.0825)
    elif d.get('t') == 2:
        z = z - (z * 0.10)  # duplicated discount logic, slightly different rate
        z = z + (z * 0.0825)
    else:
        z = z + (z * 0.0825)  # duplicated tax logic again

    return jsonify({'r': z})


# =====================================================================
# MAINTAINABILITY: Broad Exception Swallowing
# =====================================================================

@app.route('/api/webhooks/dispatch', methods=['POST'])
@require_auth
def dispatch_webhook():
    """
    MAINTAINABILITY / STABILITY — Bare Except Swallows All Errors

    Catches every possible exception (including KeyboardInterrupt-style
    and programming errors like TypeError/AttributeError) and silently
    discards them, making failures invisible and impossible to debug.
    """
    data = request.get_json()

    try:
        _ = requests.post(data['callback_url'], json=data['payload'], timeout=5)
    except:  # MAINTAINABILITY: bare except, no logging, no re-raise
        pass

    return jsonify({'status': 'dispatched'})
