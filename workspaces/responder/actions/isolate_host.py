"""Tier 1: isolate a host from the lab network. Needs on-call approval in chat."""
from _hosts import set_isolated

if __name__ == "__main__":
    set_isolated("isolate_host", True)
