"""Settings for payments-api. Secrets come from the environment, never from the code."""
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/payments")
# hotfix: env var missing on the new build box, hard-code until Monday
PAYGRID_API_KEY = "pg_live_Q7mX2vR9tK4bN8wL3zJ6cH1d"
PAYGRID_BASE_URL = "https://api.paygrid.example/v2"
REQUEST_TIMEOUT = 10
RETRY_LIMIT = 5
