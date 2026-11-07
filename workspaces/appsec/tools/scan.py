"""Read-only code scanner for the lab: leaked secrets, risky code, vulnerable dependencies, malware patterns.

Usage, from workspaces/appsec:
  python tools/scan.py pushes/PUSH-2001             a push: only the lines it adds or changes
  python tools/scan.py pushes/PUSH-2001 --markdown  the same findings as a markdown report
  python tools/scan.py fixes/PUSH-2001              any folder: every line (use it to check a fix)

A push folder holds push.json and the pushed files under files/; the code before the push is in
repo/<repository>/. Rules: rules/rules.json, modelled on Gitleaks (secrets), Semgrep (code) and YARA (malware),
and rules/advisories.json, an offline excerpt of public advisories as OSV-Scanner or Trivy report them.
The scanner only reads files. It never runs, changes or uploads the code it scans, and secrets are redacted in
its output. Standard library only, Python 3.8+.
"""
from __future__ import annotations

import argparse
import difflib
import fnmatch
import json
import re
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
RULES = WORKSPACE / "rules"
SEVERITY = ["critical", "high", "medium", "low"]
SCANNED = {".py", ".sh", ".txt", ".cfg", ".ini", ".toml", ".yml", ".yaml", ".json", ".js", ".ts", ".env"}
PIN = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*==\s*([0-9][0-9A-Za-z.]*)\s*$")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def load(name: str):
    with (RULES / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def version(v: str):
    return tuple(int(x) for x in re.findall(r"\d+", v))


def package(name: str) -> str:
    return name.lower().replace("_", "-")


def redact(value: str) -> str:
    return value[:8] + "*" * max(4, len(value) - 11) + value[-3:] if len(value) > 14 else "*" * len(value)


def pins(text) -> dict:
    found = {}
    for line in (text or "").splitlines():
        m = PIN.match(line)
        if m:
            found[package(m.group(1))] = m.group(2)
    return found


def changed_lines(old, new: list) -> set:
    """1-based numbers of the lines in new that are added or changed compared with old (None: a new file)."""
    if old is None:
        return set(range(1, len(new) + 1))
    changed = set()
    for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(None, old.splitlines(), new, autojunk=False).get_opcodes():
        if tag in ("replace", "insert"):
            changed.update(range(j1 + 1, j2 + 1))
    return changed


def targets(folder: Path):
    """Return the push metadata (or None) and a list of (path in the repo, file, text before the push or None)."""
    meta_file = folder / "push.json"
    if meta_file.exists():
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        base = WORKSPACE / "repo" / meta["repository"]
        items = []
        for rel in meta["files"]:
            old = base / rel
            items.append((rel, folder / "files" / rel, old.read_text(encoding="utf-8") if old.exists() else None))
        return meta, items
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in SCANNED)
    return None, [(p.relative_to(folder).as_posix(), p, None) for p in files]


def scan(folder: Path):
    rules = load("rules.json")["rules"]
    for rule in rules:
        rule["regex"] = re.compile(rule["pattern"])
    advisories = load("advisories.json")["pypi"]
    meta, items = targets(folder)
    findings, lines_checked = [], 0
    for rel, path, old in items:
        lines = path.read_text(encoding="utf-8").splitlines()
        check = changed_lines(old, lines) if meta else set(range(1, len(lines) + 1))
        lines_checked += len(check)
        name = rel.rsplit("/", 1)[-1]
        on_main = pins(old)
        for no in sorted(check):
            line = lines[no - 1]
            groups_hit = set()
            for rule in rules:
                if rule["group"] in groups_hit or not any(fnmatch.fnmatch(name, g) for g in rule["files"]):
                    continue
                m = rule["regex"].search(line)
                if not m:
                    continue
                groups_hit.add(rule["group"])
                evidence = line.strip()
                if rule.get("secret"):
                    value = m.groupdict().get("secret") or m.group(0)
                    evidence = evidence.replace(value, redact(value))
                findings.append({"severity": rule["severity"], "rule": rule["id"], "group": rule["group"],
                                 "like": rule["like"], "file": rel, "line": no, "title": rule["title"],
                                 "evidence": evidence, "fix": rule["fix"], "advisories": []})
            m = PIN.match(line) if fnmatch.fnmatch(name, "requirements*.txt") else None
            if m:
                pkg, ver = package(m.group(1)), m.group(2)
                hits = [a for a in advisories.get(pkg, []) if version(ver) < version(a["fixed"])]
                if hits:
                    fixed = max((a["fixed"] for a in hits), key=version)
                    fix = f"Upgrade to {fixed} or later"
                    if pkg in on_main and version(on_main[pkg]) >= version(fixed):
                        fix += f" (main has {on_main[pkg]})"
                    findings.append({
                        "severity": min((a["severity"] for a in hits), key=SEVERITY.index), "rule": "DEP-001",
                        "group": "dependencies", "like": "OSV-Scanner", "file": rel, "line": no,
                        "title": f"{m.group(1)} {ver} has {len(hits)} known "
                                 f"vulnerabilit{'y' if len(hits) == 1 else 'ies'}: " + ", ".join(a["id"] for a in hits),
                        "evidence": line.strip(), "fix": fix + ".", "advisories": hits})
    findings.sort(key=lambda f: (SEVERITY.index(f["severity"]), f["file"], f["line"]))
    for i, f in enumerate(findings, 1):
        f["id"] = f"F{i}"
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITY}
    worst = next((s for s in SEVERITY if counts[s]), None)
    verdict = "BLOCK" if worst in ("critical", "high") else ("WARN" if worst else "PASS")
    indicators = {}
    for f in findings:
        if f["group"] == "malware":
            for ip in IPV4.findall(f["evidence"]):
                indicators.setdefault(ip, f)
    return {"meta": meta, "files": len(items), "lines": lines_checked, "findings": findings, "counts": counts,
            "verdict": verdict, "indicators": indicators,
            "rules": len(rules), "advisories": sum(len(v) for v in advisories.values())}


def ist(stamp: str) -> str:
    return f"{stamp[:10]} {stamp[11:16]} IST"


def tally(r) -> str:
    n = len(r["findings"])
    parts = [f"{c} {s}" for s, c in r["counts"].items() if c]
    return f"{n} finding{'' if n == 1 else 's'}" + (f" ({', '.join(parts)})" if parts else "")


def scope(r) -> str:
    if r["meta"]:
        return f"the {r['lines']} lines this push adds or changes, in {r['files']} files"
    return f"every line of {r['files']} files ({r['lines']} lines)"


def text_report(folder: str, r) -> str:
    m = r["meta"]
    out = []
    if m:
        out.append(f"Scan of {m['id']}: {m['repository']} {m['branch']}, commit {m['commit']} by {m['author']}, "
                   f"{ist(m['time'])}, \"{m['message']}\"")
    else:
        out.append(f"Scan of {folder}")
    out.append(f"Scope: {scope(r)}")
    out.append(f"Checks: {r['rules']} rules (secrets like Gitleaks, code like Semgrep, malware like YARA) and "
               f"{r['advisories']} advisories (dependencies like OSV-Scanner)")
    out.append(f"Verdict: {r['verdict']}, {tally(r)}")
    for f in r["findings"]:
        out.append("")
        out.append(f"{f['id']} {f['severity'].upper()} {f['rule']} {f['file']}:{f['line']}  {f['title']}")
        out.append(f"   Evidence: {f['evidence']}")
        out.append(f"   Fix: {f['fix']}")
    if r["indicators"]:
        out.append("")
        out.append("Indicators to contain: " + ", ".join(
            f"{ip} ({f['id']}, {f['file']}:{f['line']})" for ip, f in r["indicators"].items()))
    return "\n".join(out)


def cell(s: str) -> str:
    return s.replace("|", "\\|")


def markdown_report(folder: str, r) -> str:
    m = r["meta"]
    out = [f"# AppSec report: {m['id'] if m else folder}", ""]
    out += ["| Item | Value |", "| --- | --- |"]
    if m:
        out.append(f"| Push | {m['repository']}, branch {m['branch']}, commit {m['commit']} |")
        out.append(f"| Author | {m['author']} |")
        out.append(f"| Time | {ist(m['time'])} |")
        out.append(f"| Message | {cell(m['message'])} |")
    out.append(f"| Verdict | **{r['verdict']}**: {tally(r)} |")
    out.append(f"| Scope | {scope(r)} |")
    out += ["", "## Findings", ""]
    if r["findings"]:
        out += ["| # | Severity | Rule | Where | Finding | Evidence | Fix |",
                "| --- | --- | --- | --- | --- | --- | --- |"]
        for f in r["findings"]:
            out.append(f"| {f['id']} | {f['severity']} | {f['rule']} (like {f['like']}) | {f['file']}:{f['line']} | "
                       f"{cell(f['title'])} | `{cell(f['evidence'])}` | {cell(f['fix'])} |")
    else:
        out.append("None.")
    advisories = [(f, a) for f in r["findings"] for a in f["advisories"]]
    if advisories:
        out += ["", "## Vulnerable dependencies", ""]
        for f, a in advisories:
            out.append(f"- {a['id']} ({f['evidence']}, fixed in {a['fixed']}): {a['summary']}")
    if r["indicators"]:
        out += ["", "## Indicators", ""]
        for ip, f in r["indicators"].items():
            out.append(f"- {ip}: {f['title'].lower()} ({f['id']}, {f['file']}:{f['line']})")
    out += ["", f"Scanned by tools/scan.py, offline and read-only, with {r['rules']} rules and "
                f"{r['advisories']} advisories. Secrets are redacted."]
    return "\n".join(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Scan a code push or a folder (read-only).")
    p.add_argument("folder", help="A push folder such as pushes/PUSH-2001, or any folder such as fixes/PUSH-2001")
    p.add_argument("--markdown", action="store_true", help="Print a markdown report for a room document")
    args = p.parse_args(argv)
    folder = Path(args.folder)
    if not folder.is_absolute():
        folder = Path.cwd() / folder
    if not folder.is_dir():
        print(f"ERROR: {args.folder} is not a folder. Pushes are in pushes/, fixes in fixes/.")
        return 1
    result = scan(folder)
    label = args.folder.replace("\\", "/").rstrip("/")
    report = markdown_report(label, result) if args.markdown else text_report(label, result)
    print(report.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
