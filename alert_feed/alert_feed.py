"""Optional: post the sample alerts into #soc-shift as a custom agent on the Switch agent protocol.

This replaces the soc-siem Claude Code agent with a plain Python program, which shows a non-LLM system (a SIEM)
joining the Switch room. Standard library only. It is a stretch goal: the demo works without it.

Endpoints used (from the Switch agent protocol docs):
  GET  /health                               check the server address
  POST /agents                               register once, with a registration key -> {id, api_key}
  GET  /agents/<agent_id>/ops                list operations
  POST /agents/<agent_id>/ops/<operation>    call an operation (body = the arguments object)
  POST /agents/<agent_id>/message            post {room_id, content}; needs no connection

Configuration comes from environment variables, or from alert_feed/.env (git-ignored):
  SWITCH_URL               server address Switch Console uses, default http://127.0.0.1:8000
  SWITCH_REGISTRATION_KEY  registration-type API key from the Gateway's API Keys page (register only)
  SWITCH_AGENT_ID          from register
  SWITCH_AGENT_KEY         from register (shown once: keep it secret)
  SWITCH_ROOM_ID           the #soc-shift room id (see the "call list_rooms" command)

Commands:
  python alert_feed/alert_feed.py health
  python alert_feed/alert_feed.py register [--name soc-alert-feed] [--save]
  python alert_feed/alert_feed.py ops
  python alert_feed/alert_feed.py call list_rooms "{}"
  python alert_feed/alert_feed.py post "text to post"
  python alert_feed/alert_feed.py play [--delay 20] [--mention @triage] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENV_FILE = HERE / ".env"
DEFAULT_ALERTS = ROOT / "workspaces" / "alert-sim" / "alerts" / "night-1"


def load_env() -> dict:
    cfg = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("SWITCH_URL", "SWITCH_REGISTRATION_KEY", "SWITCH_AGENT_ID", "SWITCH_AGENT_KEY", "SWITCH_ROOM_ID"):
        if os.environ.get(k):
            cfg[k] = os.environ[k]
    cfg.setdefault("SWITCH_URL", "http://127.0.0.1:8000")
    cfg["SWITCH_URL"] = cfg["SWITCH_URL"].rstrip("/")
    return cfg


def need(cfg: dict, *keys: str) -> None:
    missing = [k for k in keys if not cfg.get(k)]
    if missing:
        sys.exit(f"Missing {', '.join(missing)}: set them in alert_feed/.env or the environment (see .env.example)")


def http(cfg: dict, method: str, path: str, token: str = "", body=None, headers=None):
    url = cfg["SWITCH_URL"] + path
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(raw) if raw.strip().startswith(("{", "[")) else raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        return e.code, raw
    except urllib.error.URLError as e:
        sys.exit(f"Cannot reach {url}: {e.reason}. Is Switch Console's server running, and is SWITCH_URL its address?")


def show(status, payload) -> int:
    print(f"HTTP {status}")
    print(json.dumps(payload, indent=2) if not isinstance(payload, str) else payload)
    return 0 if 200 <= int(status) < 300 else 1


def format_alert(a: dict, mention: str) -> str:
    when = a.get("time", "")
    try:
        when = datetime.fromisoformat(when).strftime("%Y-%m-%d %H:%M") + " IST"
    except ValueError:
        pass
    lines = [f"{mention} New alert {a['id']} (severity from SIEM: {a.get('siem_severity', 'unknown')})",
             f"Time: {when}", f"Rule: {a.get('rule', '')}"]
    src, tgt, tip = a.get("source_ip"), a.get("target"), a.get("target_ip")
    if src or tgt:
        lines.append(f"Source: {src or '-'} -> Target: {tgt or '-'}" + (f" ({tip})" if tip else ""))
    lines.append(f"Details: {a.get('details', '')}")
    return "\n".join(lines)


def cmd_health(cfg, _a) -> int:
    return show(*http(cfg, "GET", "/health"))


def cmd_register(cfg, a) -> int:
    need(cfg, "SWITCH_REGISTRATION_KEY")
    body = {
        "name": a.name,
        "description": "Replays SIEM alerts into the SOC room (SOC Shift Relay demo)",
        "connector_type": "python-alert-feed",
        "integration_profile": {
            "connection_model": a.connection_model,
            "message_exchange": True,
            "pre_invocation_mediation": [],
            "post_invocation_mediation": [],
            "event_reporting": [],
        },
    }
    status, payload = http(cfg, "POST", "/agents", cfg["SWITCH_REGISTRATION_KEY"], body)
    if status == 409:
        print("HTTP 409: an agent with this name already exists. Reuse its saved key, or pick another --name.")
        return 1
    if not (200 <= status < 300) or not isinstance(payload, dict):
        return show(status, payload)
    print(f"Registered agent id: {payload.get('id')}")
    print("The API key is shown once. Keep it secret.")
    if a.save:
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
        lines = [l for l in lines if not l.startswith(("SWITCH_AGENT_ID=", "SWITCH_AGENT_KEY="))]
        lines += [f"SWITCH_AGENT_ID={payload.get('id')}", f"SWITCH_AGENT_KEY={payload.get('api_key')}"]
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Saved id and key to {ENV_FILE.name} (git-ignored).")
    else:
        print(f"API key: {payload.get('api_key')}")
        print("Re-run with --save to write it to alert_feed/.env instead of printing it.")
    return 0


def cmd_ops(cfg, _a) -> int:
    need(cfg, "SWITCH_AGENT_ID", "SWITCH_AGENT_KEY")
    status, payload = http(cfg, "GET", f"/agents/{cfg['SWITCH_AGENT_ID']}/ops", cfg["SWITCH_AGENT_KEY"])
    if isinstance(payload, dict) and isinstance(payload.get("operations"), dict):
        for name, spec in sorted(payload["operations"].items()):
            print(f"{name:<32} {str(spec.get('description', ''))[:90]}")
        return 0
    return show(status, payload)


def cmd_call(cfg, a) -> int:
    need(cfg, "SWITCH_AGENT_ID", "SWITCH_AGENT_KEY")
    try:
        args = json.loads(a.args)
    except json.JSONDecodeError as e:
        sys.exit(f"Arguments must be a JSON object: {e}")
    return show(*http(cfg, "POST", f"/agents/{cfg['SWITCH_AGENT_ID']}/ops/{a.operation}", cfg["SWITCH_AGENT_KEY"], args))


def post(cfg, content: str):
    return http(cfg, "POST", f"/agents/{cfg['SWITCH_AGENT_ID']}/message", cfg["SWITCH_AGENT_KEY"],
                {"room_id": cfg["SWITCH_ROOM_ID"], "content": content})


def cmd_post(cfg, a) -> int:
    need(cfg, "SWITCH_AGENT_ID", "SWITCH_AGENT_KEY", "SWITCH_ROOM_ID")
    return show(*post(cfg, a.text))


def cmd_play(cfg, a) -> int:
    files = sorted(Path(a.dir).glob("*.json"))
    if not files:
        sys.exit(f"No alert files in {a.dir}")
    if not a.dry_run:
        need(cfg, "SWITCH_AGENT_ID", "SWITCH_AGENT_KEY", "SWITCH_ROOM_ID")
    for i, f in enumerate(files):
        alert = json.loads(f.read_text(encoding="utf-8"))
        text = format_alert(alert, a.mention)
        if a.dry_run:
            print(text + "\n")
            continue
        status, payload = post(cfg, text)
        print(f"{alert['id']}: HTTP {status}")
        if not (200 <= int(status) < 300):
            print(payload)
            return 1
        if i < len(files) - 1:
            time.sleep(a.delay)
    if not a.dry_run:
        post(cfg, f"Night feed complete: {len(files)} alerts replayed.")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="SOC Shift Relay alert feed: a custom agent on the Switch protocol.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health", help="Check the server address")
    r = sub.add_parser("register", help="Register this feed as an agent (once)")
    r.add_argument("--name", default="soc-alert-feed")
    r.add_argument("--connection-model", default="session_passive",
                   choices=["always_on", "session_addressable", "auto_session", "session_passive"],
                   help="It only posts and never listens, so passive is the closest fit")
    r.add_argument("--save", action="store_true", help="Write the id and key to alert_feed/.env")
    sub.add_parser("ops", help="List the operations this agent can call")
    c = sub.add_parser("call", help="Call an operation, for example list_rooms")
    c.add_argument("operation")
    c.add_argument("args", nargs="?", default="{}", help="JSON object of arguments")
    po = sub.add_parser("post", help="Post one message into the room")
    po.add_argument("text")
    pl = sub.add_parser("play", help="Post every alert file in order")
    pl.add_argument("--dir", default=str(DEFAULT_ALERTS))
    pl.add_argument("--delay", type=float, default=20.0, help="Seconds between alerts (default 20)")
    pl.add_argument("--mention", default="@triage", help="Who each alert is addressed to (default @triage)")
    pl.add_argument("--dry-run", action="store_true", help="Print the messages instead of posting them")
    a = p.parse_args(argv)
    cfg = load_env()
    return {"health": cmd_health, "register": cmd_register, "ops": cmd_ops, "call": cmd_call,
            "post": cmd_post, "play": cmd_play}[a.cmd](cfg, a)


if __name__ == "__main__":
    raise SystemExit(main())
