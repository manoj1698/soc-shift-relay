"""Order lookups for payments-api."""
from app.db import get_cursor


def get_order(order_id):
    cur = get_cursor()
    cur.execute("SELECT id, amount, status FROM orders WHERE id = %s", (order_id,))
    return cur.fetchone()
