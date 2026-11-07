"""Tier 1: add an external IP to the lab firewall blocklist. Needs on-call approval in chat."""
from __future__ import annotations

import ipaddress

from _common import STATE, audit, check_ticket, done, fail, ip_protection_reason, parser, refuse

ACTION = "block_ip"


def main() -> None:
    args = parser("Block an IP in the lab firewall blocklist.", "IPv4 or IPv6 address").parse_args()
    check_ticket(args.ticket)
    try:
        ip = str(ipaddress.ip_address(args.target.strip()))
    except ValueError:
        fail(f"{args.target!r} is not an IP address")
    why = ip_protection_reason(ip)
    if why:
        refuse(ACTION, ip, args, why)
    path = STATE / "blocklist.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    if ip in (line.strip() for line in lines):
        audit(ACTION, ip, args, "no-op", "already blocked")
        done(f"{ip} was already on the blocklist. Nothing changed.")
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(ip + "\n")
    audit(ACTION, ip, args, "done")
    done(f"{ip} added to the blocklist ({args.ticket}).")


if __name__ == "__main__":
    main()
