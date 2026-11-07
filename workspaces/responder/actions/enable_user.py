"""Tier 1: re-enable an account in the lab directory (rollback). Needs on-call approval in chat."""
from _accounts import set_status

if __name__ == "__main__":
    set_status("enable_user", "active")
