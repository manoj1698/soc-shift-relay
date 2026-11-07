"""Tests for the lab scripts, the lookup tool, the reset script and the template builder.

Run from the repo root:  python -m unittest discover -s tests -v
Every test works on a temporary copy of the repo, so the real lab state is never touched.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ("triage", "responder", "scribe", "appsec", "alert-sim")


def run(script: Path, *args: str, cwd: Path, env=None):
    proc = subprocess.run([sys.executable, str(script), *args], cwd=str(cwd),
                          capture_output=True, text=True, encoding="utf-8", env=env)
    return proc.returncode, proc.stdout + proc.stderr


class RepoCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="soc-relay-test-"))
        self.repo = self.tmp / "repo"
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.tmp"))
        self.resp = self.repo / "workspaces" / "responder"
        self.triage = self.repo / "workspaces" / "triage"
        self.appsec = self.repo / "workspaces" / "appsec"
        self.scribe = self.repo / "workspaces" / "scribe"
        for f in (self.resp / "seed").iterdir():  # start from seed even if a rehearsal changed the live lab
            shutil.copyfile(f, self.resp / "state" / f.name)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def act(self, name: str, *args: str):
        return run(self.resp / "actions" / f"{name}.py", *args, cwd=self.resp)

    def audit(self):
        text = (self.resp / "state" / "audit.log").read_text(encoding="utf-8")
        return [json.loads(l) for l in text.splitlines() if l.strip()]


class TestActions(RepoCopy):
    T = ["--ticket", "SOC-2041", "--reason", "test"]

    def test_block_and_unblock_external_ip(self):
        code, out = self.act("block_ip", "203.0.113.45", *self.T, "--approved-by", "Manoj")
        self.assertEqual(code, 0, out)
        self.assertIn("203.0.113.45", (self.resp / "state" / "blocklist.txt").read_text(encoding="utf-8"))
        self.assertEqual(self.audit()[-1]["result"], "done")
        self.assertEqual(self.audit()[-1]["approved_by"], "Manoj")
        code, out = self.act("block_ip", "203.0.113.45", *self.T)
        self.assertEqual(code, 0, out)
        self.assertIn("already", out)
        code, out = self.act("unblock_ip", "203.0.113.45", *self.T)
        self.assertEqual(code, 0, out)
        self.assertNotIn("203.0.113.45", (self.resp / "state" / "blocklist.txt").read_text(encoding="utf-8"))

    def test_refuses_protected_ips(self):
        for ip in ("10.0.5.20", "192.0.2.80", "192.168.1.10", "127.0.0.1"):
            code, out = self.act("block_ip", ip, *self.T)
            self.assertEqual(code, 2, out)
            self.assertIn("REFUSED", out)
        self.assertNotIn("10.0.5.20", (self.resp / "state" / "blocklist.txt").read_text(encoding="utf-8"))
        self.assertTrue(all(e["result"] == "refused" for e in self.audit()))

    def test_rejects_bad_input(self):
        code, out = self.act("block_ip", "not-an-ip", *self.T)
        self.assertEqual(code, 1, out)
        code, out = self.act("block_ip", "203.0.113.45", "--ticket", "2041", "--reason", "x")
        self.assertEqual(code, 1, out)
        code, out = self.act("block_ip", "203.0.113.45")
        self.assertNotEqual(code, 0, out)

    def test_disable_enable_user_and_protected_account(self):
        code, out = self.act("disable_user", "priya.sharma", *self.T)
        self.assertEqual(code, 0, out)
        users = json.loads((self.resp / "state" / "users.json").read_text(encoding="utf-8"))
        self.assertEqual(users["priya.sharma"]["status"], "disabled")
        code, out = self.act("enable_user", "priya.sharma", *self.T)
        self.assertEqual(code, 0, out)
        code, out = self.act("disable_user", "svc-backup", *self.T)
        self.assertEqual(code, 2, out)
        code, out = self.act("disable_user", "nobody", *self.T)
        self.assertEqual(code, 1, out)

    def test_isolate_release_host_and_protected_host(self):
        code, out = self.act("isolate_host", "fin-laptop-07", *self.T)
        self.assertEqual(code, 0, out)
        hosts = json.loads((self.resp / "state" / "hosts.json").read_text(encoding="utf-8"))
        self.assertTrue(hosts["fin-laptop-07"]["isolated"])
        code, out = self.act("release_host", "fin-laptop-07", *self.T)
        self.assertEqual(code, 0, out)
        code, out = self.act("isolate_host", "scanner-01", *self.T)
        self.assertEqual(code, 2, out)

    def test_status_is_read_only(self):
        before = {p.name: p.read_bytes() for p in (self.resp / "state").iterdir()}
        code, out = self.act("status")
        self.assertEqual(code, 0, out)
        self.assertIn("Blocked IPs", out)
        after = {p.name: p.read_bytes() for p in (self.resp / "state").iterdir()}
        self.assertEqual(before, after)


class TestLookup(RepoCopy):
    def look(self, *args: str):
        return run(self.triage / "tools" / "lookup.py", *args, cwd=self.triage)

    def test_ip(self):
        code, out = self.look("ip", "203.0.113.45")
        self.assertEqual(code, 0, out)
        self.assertIn('"score": 92', out)
        self.assertIn("not protected", out)
        code, out = self.look("ip", "10.0.5.20")
        self.assertIn("PROTECTED", out)

    def test_false_positive_window(self):
        code, out = self.look("fp", "Port scan detected", "10.0.5.20", "2026-11-07T01:12:00+05:30")
        self.assertIn("MATCH FP-01", out)
        code, out = self.look("fp", "Port scan detected", "10.0.5.20", "2026-11-07T05:12:00+05:30")
        self.assertIn("NO MATCH", out)

    def test_user_and_travel(self):
        code, out = self.look("user", "priya.sharma")
        self.assertIn("XA-401", out)
        code, out = self.look("user", "ghost.user")
        self.assertIn("no record", out)


class TestRepo(RepoCopy):
    def test_reset_restores_seed(self):
        self.act("block_ip", "203.0.113.45", "--ticket", "SOC-2041", "--reason", "test")
        code, out = run(self.repo / "tools" / "reset_demo.py", cwd=self.repo)
        self.assertEqual(code, 0, out)
        for f in (self.resp / "seed").iterdir():
            self.assertEqual(f.read_bytes(), (self.resp / "state" / f.name).read_bytes(), f.name)

    def test_reset_clears_agent_output_and_restores_the_roster(self):
        roster = self.scribe / "on-call-roster.md"
        roster.write_text("changed", encoding="utf-8")
        for out_dir in (self.scribe / "reports", self.appsec / "fixes" / "PUSH-2001", self.appsec / "reports"):
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "x.md").write_text("x", encoding="utf-8")
        code, out = run(self.repo / "tools" / "reset_demo.py", cwd=self.repo)
        self.assertEqual(code, 0, out)
        self.assertEqual(roster.read_bytes(), (self.scribe / "seed" / "on-call-roster.md").read_bytes())
        for gone in (self.scribe / "reports", self.appsec / "fixes", self.appsec / "reports"):
            self.assertFalse(gone.exists(), gone)
        self.assertTrue((self.appsec / "pushes" / "PUSH-2001" / "push.json").exists())

    def test_install_agent_settings(self):
        code, out = run(self.repo / "tools" / "install_agent_settings.py", "--check", cwd=self.repo)
        if code == 0:
            self.skipTest("already installed in this checkout")
        code, out = run(self.repo / "tools" / "install_agent_settings.py", cwd=self.repo)
        self.assertEqual(code, 0, out)
        for name in AGENTS:
            ws = self.repo / "workspaces" / name
            self.assertEqual((ws / "agent-settings.json").read_text(encoding="utf-8"),
                             (ws / ".claude" / "settings.json").read_text(encoding="utf-8"))
        code, out = run(self.repo / "tools" / "install_agent_settings.py", "--check", cwd=self.repo)
        self.assertEqual(code, 0, out)

    def test_trust_marks_agent_folders_and_keeps_the_rest(self):
        cfg_dir = self.tmp / "claude-config"  # never the real ~/.claude.json
        cfg_dir.mkdir()
        (cfg_dir / ".claude.json").write_text(json.dumps({"numStartups": 3, "projects": {"/other": {"x": 1}}}),
                                              encoding="utf-8")
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg_dir))
        tool = self.repo / "tools" / "install_agent_settings.py"
        code, out = run(tool, "--trust", "--check", cwd=self.repo, env=env)
        self.assertEqual(code, 1, out)
        code, out = run(tool, "--trust", cwd=self.repo, env=env)
        self.assertEqual(code, 0, out)
        cfg = json.loads((cfg_dir / ".claude.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["numStartups"], 3)
        self.assertEqual(cfg["projects"]["/other"], {"x": 1})
        for name in AGENTS:
            key = (self.repo / "workspaces" / name).resolve().as_posix()
            self.assertIs(cfg["projects"][key]["hasTrustDialogAccepted"], True, name)
        self.assertTrue((cfg_dir / ".claude.json.bak-soc-shift-relay").exists())
        code, out = run(tool, "--trust", "--check", cwd=self.repo, env=env)
        self.assertEqual(code, 0, out)

    def test_responder_settings_gate_every_action(self):
        cfg = json.loads((ROOT / "workspaces" / "responder" / "agent-settings.json").read_text(encoding="utf-8"))
        actions = sorted(p.stem for p in (ROOT / "workspaces" / "responder" / "actions").glob("*.py")
                         if not p.stem.startswith("_") and p.stem != "status")
        for a in actions:
            self.assertIn(f"Bash(python actions/{a}.py:*)", cfg["permissions"]["ask"], a)
            self.assertNotIn(f"Bash(python actions/{a}.py:*)", cfg["permissions"].get("allow", []), a)

    def test_committed_state_matches_seed(self):
        resp = ROOT / "workspaces" / "responder"
        for f in (resp / "seed").iterdir():
            self.assertEqual(f.read_bytes(), (resp / "state" / f.name).read_bytes(),
                             f"state/{f.name} differs from seed: run python tools/reset_demo.py before committing")

    def test_runbook_lists_every_protected_target(self):
        cfg = json.loads((ROOT / "workspaces" / "responder" / "config" / "protected.json").read_text(encoding="utf-8"))
        runbook = (ROOT / "switch" / "runbook.md").read_text(encoding="utf-8")
        for key in ("protected_networks", "protected_ips", "protected_hosts", "protected_account_prefixes"):
            for item in cfg[key]:
                self.assertIn(item, runbook, f"runbook.md does not list {item} from protected.json {key}")

    def test_template_is_up_to_date(self):
        code, out = run(ROOT / "tools" / "build_template.py", "--check", cwd=ROOT)
        self.assertEqual(code, 0, out)

    def test_template_pins_claude_code(self):
        # The guardrails are Claude Code settings, and Switch Console on Windows cannot fill a provider param.
        text = (ROOT / "switch" / "soc-shift-relay.template.yaml").read_text(encoding="utf-8")
        self.assertEqual(text.count("\n    provider: claude\n"), len(AGENTS))
        self.assertNotIn("type: provider", text)

    def test_template_parses_when_pyyaml_is_available(self):
        try:
            import yaml  # type: ignore
        except ImportError:
            self.skipTest("PyYAML not installed")
        doc = yaml.safe_load((ROOT / "switch" / "soc-shift-relay.template.yaml").read_text(encoding="utf-8"))
        self.assertEqual(doc["version"], 1)
        self.assertEqual(len(doc["agents"]), len(AGENTS))
        self.assertEqual([r["name"] for r in doc["rooms"][0]["roles"]], ["triage", "responder", "scribe", "appsec"])
        self.assertEqual(len(doc["rooms"][0]["agents"]), len(AGENTS))
        responder = [a for a in doc["agents"] if a["name"].endswith("-responder")][0]
        self.assertIs(responder["auto_mode"], False)
        self.assertEqual(responder["addressing"], "owner-agents")

    def test_alerts_are_valid_json_with_required_fields(self):
        for f in sorted((ROOT / "workspaces" / "alert-sim" / "alerts" / "night-1").glob("*.json")):
            a = json.loads(f.read_text(encoding="utf-8"))
            for key in ("id", "siem_severity", "time", "rule", "details"):
                self.assertIn(key, a, f.name)


FIXED = {  # what a correct fix of PUSH-2001 looks like; the scanner must pass it
    "app/config.py": 'import os\nPAYGRID_API_KEY = os.environ["PAYGRID_API_KEY"]\nRETRY_LIMIT = 5\n',
    "app/orders.py": 'def find_orders(cur, customer_ref):\n'
                     '    cur.execute("SELECT id FROM orders WHERE customer_ref = %s", (customer_ref,))\n',
    "requirements.txt": "flask==3.0.3\nrequests==2.32.4\nPyYAML==6.0.2\npsycopg2-binary==2.9.9\n",
    "scripts/post_deploy.sh": "#!/bin/sh\nset -e\npython -m app.migrate\nsystemctl restart payments-api\n",
}


class TestScanner(RepoCopy):
    def scan(self, *args: str):
        return run(self.appsec / "tools" / "scan.py", *args, cwd=self.appsec)

    def test_push_is_blocked_with_every_planted_problem(self):
        code, out = self.scan("pushes/PUSH-2001")
        self.assertEqual(code, 0, out)
        self.assertIn("Verdict: BLOCK, 5 findings (1 critical, 3 high, 1 medium)", out)
        for expected in ("F1 CRITICAL MAL-001 scripts/post_deploy.sh:6", "SEC-001 app/config.py:6",
                         "CODE-001 app/orders.py:19", "DEP-001 requirements.txt:3", "DEP-001 requirements.txt:2",
                         "CVE-2020-14343", "CVE-2018-18074", "Indicators to contain: 198.51.100.23"):
            self.assertIn(expected, out)

    def test_secrets_never_leave_the_scanner(self):
        pushed = (self.appsec / "pushes" / "PUSH-2001" / "files" / "app" / "config.py").read_text(encoding="utf-8")
        key = [part for part in pushed.split('"') if part.startswith("pg_live_")][0]
        for args in (("pushes/PUSH-2001",), ("pushes/PUSH-2001", "--markdown")):
            code, out = self.scan(*args)
            self.assertNotIn(key, out)
            self.assertIn("pg_live_****", out)

    def test_main_before_the_push_is_clean(self):
        code, out = self.scan("repo/payments-api")
        self.assertIn("Verdict: PASS, 0 findings", out)

    def test_a_correct_fix_passes(self):
        fix = self.appsec / "fixes" / "PUSH-2001"
        for rel, text in FIXED.items():
            (fix / rel).parent.mkdir(parents=True, exist_ok=True)
            (fix / rel).write_text(text, encoding="utf-8")
        code, out = self.scan("fixes/PUSH-2001")
        self.assertIn("Verdict: PASS, 0 findings", out)

    def test_markdown_report_and_read_only(self):
        before = {p: p.read_bytes() for p in self.appsec.rglob("*") if p.is_file()}
        code, out = self.scan("pushes/PUSH-2001", "--markdown")
        self.assertEqual(code, 0, out)
        self.assertIn("# AppSec report: PUSH-2001", out)
        self.assertIn("| F1 | critical | MAL-001", out)
        self.assertIn("\\| sh", out)  # the pipe in the evidence is escaped inside the table
        after = {p: p.read_bytes() for p in self.appsec.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_missing_folder(self):
        code, out = self.scan("pushes/PUSH-9999")
        self.assertEqual(code, 1, out)

    def test_siem_push_matches_the_pushed_code(self):
        event = json.loads((ROOT / "workspaces" / "alert-sim" / "pushes" / "PUSH-2001.json").read_text(encoding="utf-8"))
        push = json.loads((ROOT / "workspaces" / "appsec" / "pushes" / "PUSH-2001" / "push.json").read_text(encoding="utf-8"))
        for key in ("id", "time", "repository", "branch", "commit", "author", "message", "files"):
            self.assertEqual(event[key], push[key], key)
        for rel in push["files"]:
            self.assertTrue((ROOT / "workspaces" / "appsec" / "pushes" / "PUSH-2001" / "files" / rel).exists(), rel)

    def test_appsec_cannot_touch_the_code_it_scans(self):
        cfg = json.loads((ROOT / "workspaces" / "appsec" / "agent-settings.json").read_text(encoding="utf-8"))
        for folder in ("pushes", "repo", "tools", "rules"):
            self.assertIn(f"Write(./{folder}/**)", cfg["permissions"]["deny"])
            self.assertIn(f"Edit(./{folder}/**)", cfg["permissions"]["deny"])
        self.assertIn("Bash(sh:*)", cfg["permissions"]["deny"])


class TestAuditTrail(RepoCopy):
    def trail(self, *args: str):
        return run(self.scribe / "tools" / "audit_trail.py", *args, cwd=self.scribe)

    def test_lists_actions_with_approver_and_filters_by_ticket(self):
        code, out = self.trail()
        self.assertEqual(code, 0, out)
        self.assertIn("no actions recorded", out)
        self.act("block_ip", "203.0.113.45", "--ticket", "SOC-2041", "--reason", "SSH brute force",
                 "--approved-by", "Manoj")
        self.act("block_ip", "10.0.5.20", "--ticket", "SOC-2040", "--reason", "test")
        code, out = self.trail()
        self.assertIn("| block_ip | 203.0.113.45 | done | SOC-2041 | Manoj | SSH brute force |", out)
        self.assertIn("refused", out)
        code, out = self.trail("--ticket", "SOC-2041")
        self.assertIn("203.0.113.45", out)
        self.assertNotIn("10.0.5.20", out)
        self.assertIn("1 audit entry for SOC-2041", out)


if __name__ == "__main__":
    unittest.main()
