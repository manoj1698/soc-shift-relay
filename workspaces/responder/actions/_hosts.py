"""Shared logic for isolate_host.py and release_host.py."""
from __future__ import annotations

from _common import STATE, audit, check_ticket, done, fail, host_protection_reason, parser, read_json, refuse, write_json


def set_isolated(action: str, isolated: bool) -> None:
    verb = "Isolate" if isolated else "Release"
    args = parser(f"{verb} a host in the lab network.", "hostname, for example fin-laptop-07").parse_args()
    check_ticket(args.ticket)
    host = args.target.strip()
    if isolated:
        why = host_protection_reason(host)
        if why:
            refuse(action, host, args, why)
    path = STATE / "hosts.json"
    hosts = read_json(path)
    if host not in hosts:
        fail(f"no host named {host!r} in the lab network")
    state = "isolated" if isolated else "connected"
    if hosts[host]["isolated"] == isolated:
        audit(action, host, args, "no-op", f"already {state}")
        done(f"{host} was already {state}. Nothing changed.")
    hosts[host]["isolated"] = isolated
    write_json(path, hosts)
    audit(action, host, args, "done")
    done(f"{host} is now {state} ({args.ticket}).")
