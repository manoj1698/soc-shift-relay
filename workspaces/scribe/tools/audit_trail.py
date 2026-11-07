"""Read-only: print the lab's containment trail (the responder's audit log) as a markdown table.

Usage, from workspaces/scribe:
  python tools/audit_trail.py                    every entry
  python tools/audit_trail.py --ticket SOC-2041  one ticket
@scribe pastes it into reports, so a report never states an action or an approver that the audit log does not
show. It only reads ../responder/state/audit.log. Standard library only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[2] / "responder" / "state" / "audit.log"


def cell(value) -> str:
    return str(value).replace("|", "\\|")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Print the lab containment trail as a markdown table (read-only).")
    p.add_argument("--ticket", help="Only the entries of this ticket, for example SOC-2041")
    args = p.parse_args(argv)
    entries = []
    if AUDIT.exists():
        entries = [json.loads(l) for l in AUDIT.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.ticket:
        entries = [e for e in entries if e.get("ticket") == args.ticket]
    print("| Time (IST) | Action | Target | Result | Ticket | Approved by | Reason |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for e in entries:
        when = e.get("time", "")[:16].replace("T", " ")
        result = e.get("result", "") + (f" ({e['detail']})" if e.get("detail") else "")
        print("| " + " | ".join(cell(v) for v in (when, e.get("action", ""), e.get("target", ""), result,
                                                   e.get("ticket", ""), e.get("approved_by", ""),
                                                   e.get("reason", ""))) + " |")
    if not entries:
        print("| - | no actions recorded | - | - | - | - | - |")
    scope = f" for {args.ticket}" if args.ticket else ""
    print(f"\n{len(entries)} audit entr{'y' if len(entries) == 1 else 'ies'}{scope}, from the lab audit log.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
