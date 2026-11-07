"""Database connection for payments-api."""
import psycopg2

from app.config import DATABASE_URL


def get_cursor():
    return psycopg2.connect(DATABASE_URL).cursor()
