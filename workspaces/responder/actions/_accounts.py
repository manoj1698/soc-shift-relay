"""Shared logic for disable_user.py and enable_user.py."""
from __future__ import annotations

from _common import STATE, account_protection_reason, audit, check_ticket, done, fail, parser, read_json, refuse, write_json


def set_status(action: str, new_status: str) -> None:
    verb = "Disable" if new_status == "disabled" else "Re-enable"
    args = parser(f"{verb} an account in the lab directory.", "username, for example priya.sharma").parse_args()
    check_ticket(args.ticket)
    user = args.target.strip()
    if new_status == "disabled":
        why = account_protection_reason(user)
        if why:
            refuse(action, user, args, why)
    path = STATE / "users.json"
    users = read_json(path)
    if user not in users:
        fail(f"no account named {user!r} in the lab directory")
    if users[user]["status"] == new_status:
        audit(action, user, args, "no-op", f"already {new_status}")
        done(f"{user} was already {new_status}. Nothing changed.")
    users[user]["status"] = new_status
    write_json(path, users)
    audit(action, user, args, "done")
    done(f"{user} is now {new_status} ({args.ticket}).")
