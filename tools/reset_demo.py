"""Reset the lab before a rehearsal or the recording.

Restores workspaces/responder/state/ from seed/, clears the scribe's local shift-log mirror, restores the
on-call roster mirror, and removes what agents wrote during a run: @scribe's reports/ and @appsec's fixes/ and
reports/. It does not touch Switch: also clear the room (or use a fresh room) so old messages do not confuse
the agents.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WS = ROOT / "workspaces"
RESPONDER = WS / "responder"
SCRIBE = WS / "scribe"
SCRIBE_LOG = SCRIBE / "shift-log.md"
EMPTY_LOG = "# Shift log\n\n(Empty. @scribe writes this mirror of the shift-log room document.)\n"
AGENT_OUTPUT = [SCRIBE / "reports", WS / "appsec" / "fixes", WS / "appsec" / "reports"]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Reset the SOC Shift Relay lab to its starting state.")
    p.add_argument("--keep-log", action="store_true", help="Keep the scribe's local shift-log.md")
    args = p.parse_args(argv)

    seed, state = RESPONDER / "seed", RESPONDER / "state"
    state.mkdir(exist_ok=True)
    for f in sorted(seed.iterdir()):
        if f.is_file():
            shutil.copyfile(f, state / f.name)
            print(f"restored state/{f.name}")
    if not args.keep_log:
        SCRIBE_LOG.write_text(EMPTY_LOG, encoding="utf-8")
        print("cleared workspaces/scribe/shift-log.md")
    shutil.copyfile(SCRIBE / "seed" / "on-call-roster.md", SCRIBE / "on-call-roster.md")
    print("restored workspaces/scribe/on-call-roster.md")
    for folder in AGENT_OUTPUT:
        if folder.exists():
            shutil.rmtree(folder)
            print(f"removed {folder.relative_to(ROOT).as_posix()}/")
    print("Lab reset. In Discord, start from a fresh room or ask @scribe to start a new shift-log section.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
