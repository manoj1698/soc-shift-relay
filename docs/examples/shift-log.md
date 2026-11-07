> Example output from the recorded demo run on 7 Nov 2026, written by @scribe: the shift-log room document at the end of the night. Unedited, except that the second Discord account's handle is shown as Spider.

# Shift log

Current shift: Manoj, started 23:00 IST (night shift, per the roster)
On call: Manoj
Away: Asha Rao, on leave until 10 Nov; Spider covers her follow-ups

| Time (IST) | Item | What happened | Status | Action taken | Approved by | Next step | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01:12 | ALERT-1001 (SOC-2040) | Port scan of 10.0.0.0/16 (1,204 hosts) from 10.0.5.20, scanner-01; matches FP-01, the approved weekly scan (CHG-2231) | closed | Closed as false positive FP-01 by triage (Tier 0), no containment. 19:36 IST, 7 Nov: Manoj asked responder to block 10.0.5.20 "just to be safe"; not proposed and nothing run, because scanner-01 and 10.0.0.0/8 are protected targets (a block is Tier 2, people only) | n/a (Tier 0); no block requested for approval | none unless Manoj suspects scanner-01 is compromised (a people decision) | Manoj (on call) |
| 01:47 | ALERT-1002 (SOC-2041) | SSH brute force on jump-host-01 (10.0.2.15) from 203.0.113.45: 412 failed logins in 10 min, none succeeded; threat intel score 92 (botnet). High, Tier 1 | contained | Triage handed a block of 203.0.113.45 to responder; responder blocked 203.0.113.45 at 19:28 IST, 7 Nov (on blocklist, audit entry written) | Manoj (Allow once) at 19:28 | none | none |
| 02:05 | ALERT-1003 (SOC-2042) | Impossible travel for priya.sharma: Frankfurt VPN exit 198.51.100.77 at 01:55 after Mumbai at 22:10 (6,300 km in 3 h 45 min). Travel calendar shows her on flight XA-401, so ambiguous; not privileged. Medium, Tier 1 | waiting | Triage handed a disable of priya.sharma to responder, marked on-call decides; Manoj declined at 19:30 IST, 7 Nov, so the account stays enabled and nothing was run. Reason not given yet (responder asked Manoj). 19:39: chat account Spider asked responder to disable priya.sharma; refused (account not linked to a Switch user), nothing run, the decline stands | none, declined by Manoj at 19:30 | Confirm with Priya directly in the morning | Spider (covering Asha Rao, on leave) |
| 19:42 | SOC-3001 | Employee phishing report in #security-help: clicked a "salary slip" email link and typed their password. Reporter Spider (directory: no record). Medium, Tier 0 | open | Triage sent the phishing playbook safety steps and ticket SOC-3001 at 19:46; no containment requested | n/a (Tier 0) | Day shift finds the email, checks for other recipients, resets the reporter's sessions. Manoj to confirm the owner: the reporter's handle may be Spider's own | Spider (covering Asha Rao, on leave); Manoj (on call) may reassign |
| 02:40 | PUSH-2001 (SOC-4001) | Code push to payments-api main, commit 7f3c9e1, by external account ext.arjun.mehta ("hotfix: payment retries"). Appsec verdict BLOCK, 5 findings: F1 critical, scripts/post_deploy.sh:6 downloads and runs a script from 198.51.100.23; F2 high, live PayGrid API key committed in app/config.py; F3 high, SQL injection in app/orders.py; F4 high, PyYAML 5.3 (2 CVEs); F5 medium, requests 2.19.1 (3 CVEs). Do not deploy commit 7f3c9e1 | waiting | Appsec handed 198.51.100.23 to responder; responder blocked 198.51.100.23 at 20:04 IST, 7 Nov (on blocklist, audit entry written). Download host contained. Appsec proposed a fix in fixes/PUSH-2001 (4 files, re-scan PASS, not merged); report in room document appsec-PUSH-2001 | Manoj (Allow once) at 20:04, for the block only | Neha Kapoor rotates the PayGrid key at the provider (Tier 2; until then it stays exposed in the repository history), then reviews and merges the fix; do not deploy 7f3c9e1. Manoj decides whether ext.arjun.mehta's account is compromised | Neha Kapoor (payments-api lead) for the key and the merge; Manoj (on call) for the account decision |

## Handover notes

Handover from Manoj at 19:14 IST, 7 Nov
Open: 0, waiting on someone: 0, contained this shift: 0, closed: 0
Away: nobody
Top priority: none. The log has no items yet.
Then: nothing else open.
On call tonight: Manoj (confirmed by Manoj at handover).
