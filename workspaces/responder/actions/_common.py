"""Shared helpers for the lab action scripts.

Every action script changes only files in ../state/ and appends one JSON line to ../state/audit.log.
Nothing here touches a real system or the network. Standard library only, Python 3.8+.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
STATE = WORKSPACE / "state"
CONFIG = WORKSPACE / "config"
IST = timezone(timedelta(hours=5, minutes=30), "IST")

EXIT_OK = 0
EXIT_REFUSED = 2
EXIT_ERROR = 1


def now_ist() -> str:
    return datetime.now(IST).isoformat(timespec="seconds")


def read_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=True)
        fh.write("\n")
    tmp.replace(path)


def protected() -> dict:
    return read_json(CONFIG / "protected.json")


def ip_protection_reason(ip: str):
    """Return why an IP must never be blocked, or None if blocking is allowed."""
    cfg = protected()
    addr = ipaddress.ip_address(ip)
    if ip in cfg.get("protected_ips", []):
        return f"{ip} is on the protected list"
    for net in cfg.get("protected_networks", []):
        if addr in ipaddress.ip_network(net):
            return f"{ip} is inside protected network {net}"
    return None


def account_protection_reason(username: str):
    for prefix in protected().get("protected_account_prefixes", []):
        if username.startswith(prefix):
            return f"{username} is a protected service account ({prefix}*)"
    return None


def host_protection_reason(hostname: str):
    if hostname in protected().get("protected_hosts", []):
        return f"{hostname} is a protected host"
    return None


def audit(action: str, target: str, args: argparse.Namespace, result: str, detail: str = "") -> None:
    entry = {
        "time": now_ist(),
        "action": action,
        "target": target,
        "ticket": args.ticket,
        "reason": args.reason,
        "approved_by": args.approved_by or ("see Switch approval record" if result == "done" else "-"),
        "result": result,
    }
    if detail:
        entry["detail"] = detail
    with (STATE / "audit.log").open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=True) + "\n")


def parser(description: str, target_help: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("target", help=target_help)
    p.add_argument("--ticket", required=True, help="Ticket id, for example SOC-2041")
    p.add_argument("--reason", required=True, help="Why this action is needed, in a few words")
    p.add_argument("--approved-by", default="", help="Approver name as recorded by Switch (optional)")
    return p


def check_ticket(ticket: str) -> None:
    if not ticket.startswith("SOC-") or not ticket[4:].isdigit():
        fail(f"ticket must look like SOC-2041, got {ticket!r}")


def refuse(action: str, target: str, args: argparse.Namespace, why: str) -> None:
    audit(action, target, args, "refused", why)
    print(f"REFUSED: {why}. Runbook Tier 2: people only. Nothing was changed.")
    sys.exit(EXIT_REFUSED)


def fail(message: str) -> None:
    print(f"ERROR: {message}. Nothing was changed.")
    sys.exit(EXIT_ERROR)


def done(message: str) -> None:
    print(f"DONE: {message}")
    sys.exit(EXIT_OK)
