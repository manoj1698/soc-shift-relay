"""Tier 1: reconnect an isolated host (rollback). Needs on-call approval in chat."""
from _hosts import set_isolated

if __name__ == "__main__":
    set_isolated("release_host", False)
