"""Order lookups for payments-api."""
import time

from app.config import RETRY_LIMIT
from app.db import get_cursor


def get_order(order_id):
    cur = get_cursor()
    cur.execute("SELECT id, amount, status FROM orders WHERE id = %s", (order_id,))
    return cur.fetchone()


def find_orders(customer_ref):
    # hotfix: retry while the payment gateway is slow
    cur = get_cursor()
    for attempt in range(RETRY_LIMIT):
        try:
            cur.execute("SELECT id, amount, status FROM orders WHERE customer_ref = %s", (customer_ref,))
            return cur.fetchall()
        except TimeoutError:
            time.sleep(2 ** attempt)
    return []
