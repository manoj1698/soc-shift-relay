"""Tier 1: disable an account in the lab directory. Needs on-call approval in chat."""
from _accounts import set_status

if __name__ == "__main__":
    set_status("disable_user", "disabled")
