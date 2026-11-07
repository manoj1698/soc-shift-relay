"""Read-only lookups for the triage agent. Reads ../intel/*.json and never writes anything.

Usage:
  python tools/lookup.py ip 203.0.113.45
  python tools/lookup.py user priya.sharma
  python tools/lookup.py host jump-host-01
  python tools/lookup.py fp "Port scan detected" 10.0.5.20 2026-11-07T01:12:00+05:30
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

INTEL = Path(__file__).resolve().parent.parent / "intel"
IST = timezone(timedelta(hours=5, minutes=30))


def load(name: str):
    with (INTEL / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def show(title: str, data) -> None:
    print(title)
    print(json.dumps(data, indent=2, ensure_ascii=True))


def protection_of_ip(ip: str):
    allow = load("allowlist.json")
    if ip in allow["protected_ips"]:
        return "PROTECTED: " + allow["protected_ips"][ip]
    addr = ipaddress.ip_address(ip)
    for net in allow["protected_networks"]:
        if addr in ipaddress.ip_network(net):
            return f"PROTECTED: inside internal network {net}"
    return "not protected"


def cmd_ip(value: str) -> int:
    try:
        ip = str(ipaddress.ip_address(value))
    except ValueError:
        print(f"ERROR: {value!r} is not an IP address")
        return 1
    intel = load("threat-intel.json")["ips"].get(ip)
    print(f"IP {ip}")
    print(f"Protection: {protection_of_ip(ip)}")
    if intel:
        show("Threat intel:", intel)
    else:
        print("Threat intel: no record (treat as unknown)")
    return 0


def cmd_user(value: str) -> int:
    user = load("directory.json")["users"].get(value)
    if not user:
        print(f"User {value}: no record")
        return 0
    prefixes = load("allowlist.json")["protected_account_prefixes"]
    protected = any(value.startswith(p) for p in prefixes)
    show(f"User {value}" + (" (PROTECTED service account)" if protected else ""), user)
    trips = [t for t in load("travel-calendar.json")["trips"] if t["user"] == value]
    if trips:
        show("Travel calendar:", trips)
    else:
        print("Travel calendar: no trips on record")
    return 0


def cmd_host(value: str) -> int:
    host = load("directory.json")["hosts"].get(value)
    if not host:
        print(f"Host {value}: no record")
        return 0
    show(f"Host {value}", host)
    return 0


def cmd_fp(rule: str, source_ip: str, when: str) -> int:
    try:
        t = datetime.fromisoformat(when)
    except ValueError:
        print(f"ERROR: time {when!r} is not ISO format, for example 2026-11-07T01:12:00+05:30")
        return 1
    if t.tzinfo is None:
        t = t.replace(tzinfo=IST)
    t = t.astimezone(IST)
    day, hhmm = t.strftime("%a"), t.strftime("%H:%M")
    for r in load("known-false-positives.json")["rules"]:
        start, end = r["window_ist"]
        if (r["rule"].lower() == rule.lower() and r["source_ip"] == source_ip
                and day in r["weekdays"] and start <= hhmm <= end):
            print(f"MATCH {r['id']}: {r['reason']} (change ticket {r['change_ticket']}). "
                  f"Rule, source and window ({'/'.join(r['weekdays'])} {start}-{end} IST) all match.")
            return 0
    print(f"NO MATCH: no known false-positive rule covers {rule!r} from {source_ip} on {day} {hhmm} IST")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Read-only lookups for triage.")
    sub = p.add_subparsers(dest="kind", required=True)
    for kind in ("ip", "user", "host"):
        sub.add_parser(kind).add_argument("value")
    fp = sub.add_parser("fp", help="Check a known false-positive rule")
    fp.add_argument("rule")
    fp.add_argument("source_ip")
    fp.add_argument("time", help="Alert time, ISO format")
    a = p.parse_args(argv)
    if a.kind == "ip":
        return cmd_ip(a.value)
    if a.kind == "user":
        return cmd_user(a.value)
    if a.kind == "host":
        return cmd_host(a.value)
    return cmd_fp(a.rule, a.source_ip, a.time)


if __name__ == "__main__":
    sys.exit(main())
