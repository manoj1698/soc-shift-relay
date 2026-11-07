"""Install each agent's Claude Code permission settings, and optionally trust the agent folders.

Copies workspaces/<agent>/agent-settings.json to workspaces/<agent>/.claude/settings.json, the project settings
file Claude Code reads when Switch Console starts the agent in that folder. Run once after cloning, and again
after you change an agent-settings.json. Use --check to only report whether they are installed and current.

--trust also marks the agent folders as trusted in Claude Code's own config (~/.claude.json, or the one in
CLAUDE_CONFIG_DIR). Claude Code ignores a folder's permissions.allow rules until the folder is trusted, and
Switch starts agents without the interactive trust dialog. Deny and ask rules apply either way. The config is
backed up once, next to it, as .claude.json.bak-soc-shift-relay.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ["triage", "responder", "scribe", "appsec", "alert-sim"]


def claude_config() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home()) / ".claude.json"


def folder_key(name: str) -> str:
    # The form Claude Code uses for its projects map, for example D:/repo/workspaces/triage
    return (ROOT / "workspaces" / name).resolve().as_posix()


def trust_folders(check: bool) -> int:
    path = claude_config()
    config = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    projects = config.setdefault("projects", {})
    missing = [n for n in AGENTS if not projects.get(folder_key(n), {}).get("hasTrustDialogAccepted")]
    for name in AGENTS:
        state = "trusted" if name not in missing else ("NOT trusted" if check else "now trusted")
        print(f"{name:<10} {state:<12} workspaces/{name}")
    if check:
        if missing:
            print("Run: python tools/install_agent_settings.py --trust")
        return 1 if missing else 0
    if not missing:
        return 0
    backup = path.with_name(path.name + ".bak-soc-shift-relay")
    if path.exists() and not backup.exists():
        shutil.copyfile(path, backup)
    for name in missing:
        projects.setdefault(folder_key(name), {})["hasTrustDialogAccepted"] = True
    tmp = path.with_name(path.name + ".tmp-soc-shift-relay")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(config, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    tmp.replace(path)
    print(f"Updated Claude Code's config ({path.name}); backup: {backup.name}")
    print("Agents already running keep the old view: restart them (!reset) so their allow rules load.")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Install the agents' Claude Code permission settings.")
    p.add_argument("--check", action="store_true", help="Only report; exit 1 if any is missing or stale")
    p.add_argument("--trust", action="store_true",
                   help="Also mark the agent folders as trusted in Claude Code's config, so their allow rules apply")
    args = p.parse_args(argv)
    stale = 0
    for name in AGENTS:
        src = ROOT / "workspaces" / name / "agent-settings.json"
        dst = ROOT / "workspaces" / name / ".claude" / "settings.json"
        text = src.read_text(encoding="utf-8")
        json.loads(text)  # refuse to install broken JSON
        current = dst.exists() and dst.read_text(encoding="utf-8") == text
        if args.check:
            print(f"{name:<10} {'ok' if current else 'MISSING or out of date'}")
            stale += 0 if current else 1
            continue
        dst.parent.mkdir(exist_ok=True)
        with dst.open("w", encoding="utf-8", newline="\n") as fh:  # write_text has no newline= before 3.10
            fh.write(text)
        print(f"{name:<10} installed .claude/settings.json")
    code = 0
    if args.check and stale:
        print("Run: python tools/install_agent_settings.py")
        code = 1
    if args.trust:
        code = max(code, trust_folders(args.check))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
