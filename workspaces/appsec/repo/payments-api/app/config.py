"""Settings for payments-api. Secrets come from the environment, never from the code."""
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/payments")
PAYGRID_API_KEY = os.environ["PAYGRID_API_KEY"]
PAYGRID_BASE_URL = "https://api.paygrid.example/v2"
REQUEST_TIMEOUT = 10
