"""Read-only: show the lab's current containment state and the last audit entries. No approval needed."""
from __future__ import annotations

import argparse
import json

from _common import STATE, read_json


def main() -> None:
    p = argparse.ArgumentParser(description="Show the lab containment state (read-only).")
    p.add_argument("--audit", type=int, default=5, help="How many recent audit entries to show (default 5)")
    args = p.parse_args()

    blocked = [l.strip() for l in (STATE / "blocklist.txt").read_text(encoding="utf-8").splitlines()
               if l.strip() and not l.startswith("#")]
    users = read_json(STATE / "users.json")
    hosts = read_json(STATE / "hosts.json")
    disabled = sorted(u for u, v in users.items() if v["status"] != "active")
    isolated = sorted(h for h, v in hosts.items() if v["isolated"])

    print("Blocked IPs:      " + (", ".join(blocked) if blocked else "none"))
    print("Disabled accounts: " + (", ".join(disabled) if disabled else "none"))
    print("Isolated hosts:   " + (", ".join(isolated) if isolated else "none"))

    lines = [l for l in (STATE / "audit.log").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"Last {min(args.audit, len(lines))} of {len(lines)} audit entries:")
    if not lines:
        print("  (none)")
    for line in lines[-args.audit:]:
        e = json.loads(line)
        print(f"  {e['time']}  {e['action']:<13} {e['target']:<16} {e['result']:<8} "
              f"{e['ticket']}  approved by: {e['approved_by']}")


if __name__ == "__main__":
    main()
