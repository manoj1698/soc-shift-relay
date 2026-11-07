"""Tier 1: remove an IP from the lab firewall blocklist (rollback). Needs on-call approval in chat."""
from __future__ import annotations

import ipaddress

from _common import STATE, audit, check_ticket, done, fail, parser

ACTION = "unblock_ip"


def main() -> None:
    args = parser("Remove an IP from the lab firewall blocklist.", "IPv4 or IPv6 address").parse_args()
    check_ticket(args.ticket)
    try:
        ip = str(ipaddress.ip_address(args.target.strip()))
    except ValueError:
        fail(f"{args.target!r} is not an IP address")
    path = STATE / "blocklist.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    kept = [line for line in lines if line.strip() != ip]
    if len(kept) == len(lines):
        audit(ACTION, ip, args, "no-op", "not on the blocklist")
        done(f"{ip} was not on the blocklist. Nothing changed.")
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    audit(ACTION, ip, args, "done")
    done(f"{ip} removed from the blocklist ({args.ticket}).")


if __name__ == "__main__":
    main()
