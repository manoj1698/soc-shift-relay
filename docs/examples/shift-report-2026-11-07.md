> Example output from the recorded demo run on 7 Nov 2026, written by @scribe: the report-2026-11-07 room document. Unedited, except that the second Discord account's handle is shown as Spider.

# Shift report: night of 6-7 Nov 2026
Prepared by @scribe at 20:14 IST, 7 Nov, from the shift log, the roster and the audit log. Requested by Spider (chat account, not linked to a Switch user).

## Summary
Five items came in for the night of 6-7 Nov: three alerts, one code push and one employee report. One alert was a known false positive, and two attacker addresses were blocked with Manoj's approval: the SSH brute-force source and the download host in a malicious code push to payments-api. Still open: a morning check with Priya Sharma after Manoj declined to disable her account, an employee phishing follow-up for the day shift, and the leaked payment key in the push, which Neha Kapoor must rotate before the fix is merged.

## Items
| Time (IST) | Item | Severity | Outcome | Approved by | Owner |
| --- | --- | --- | --- | --- | --- |
| 01:12 | ALERT-1001 (SOC-2040): port scan of 10.0.0.0/16 from scanner-01 (10.0.5.20) | Low | Closed as false positive FP-01, the approved weekly scan (CHG-2231). A later request to block 10.0.5.20 was refused as a protected target; nothing run | n/a (Tier 0) | none |
| 01:47 | ALERT-1002 (SOC-2041): SSH brute force on jump-host-01 from 203.0.113.45, 412 failed logins, none succeeded | High | Contained: 203.0.113.45 blocked at 19:28 | Manoj (Allow once) | none |
| 02:05 | ALERT-1003 (SOC-2042): impossible travel for priya.sharma, Frankfurt VPN login at 01:55 while the calendar shows her on flight XA-401 | Medium | Disable declined by Manoj at 19:30; account stays enabled; waiting for the morning check | none (declined) | Spider (covering Asha Rao, on leave) |
| 02:40 | PUSH-2001 (SOC-4001): push to payments-api main, commit 7f3c9e1, by ext.arjun.mehta | Critical (verdict BLOCK, 5 findings) | 198.51.100.23 (download-and-execute host) blocked at 20:04. Fix ready in fixes/PUSH-2001, re-scan PASS, not merged. Leaked PayGrid key still to be rotated. Do not deploy 7f3c9e1 | Manoj (Allow once), for the block | Neha Kapoor; Manoj for the account decision |
| 19:42 | SOC-3001: employee phishing report in #security-help, link clicked and password typed (reporter Spider) | Medium | Safety steps given at 19:46; open for the day shift | n/a (Tier 0) | Spider (covering Asha Rao, on leave); Manoj to confirm the owner |

## Containment actions (from the audit log)
| Time (IST) | Action | Target | Result | Ticket | Approved by | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-07 19:28 | block_ip | 203.0.113.45 | done | SOC-2041 | Manoj | SSH brute force |
| 2026-11-07 20:04 | block_ip | 198.51.100.23 | done | SOC-4001 | Manoj | Download-and-execute host in PUSH-2001 |

2 audit entries, from the lab audit log.

## Open follow-ups
| Next step | Owner | Due |
| --- | --- | --- |
| SOC-3001: find the email, check for other recipients, reset the reporter's sessions | Spider (covering Asha Rao, on leave); Manoj to confirm the owner, as the reporter may be Spider | Day shift |
| ALERT-1003: confirm with Priya directly | Spider (covering Asha Rao, on leave) | Morning |
| PUSH-2001: rotate the PayGrid key at the provider (Tier 2); it stays exposed in the repository history until then | Neha Kapoor (payments-api lead) | Not set |
| PUSH-2001: review and merge the fix in fixes/PUSH-2001; do not deploy commit 7f3c9e1 | Neha Kapoor (payments-api lead) | Not set; before any deploy |
| PUSH-2001: decide whether ext.arjun.mehta's account is compromised | Manoj (on call) | Not set |
| ALERT-1003: record the reason for the decline | Manoj (on call) | Not set |

## Lessons and recommendations
- PUSH-2001 reached main from an external account with a download-and-run script and a live payment key; only the scan stopped it. A review step before external accounts can push to main would catch this earlier.
- The chat account Spider has no directory record and is not linked to a Switch user, yet it reported a phishing compromise and asked for a containment action. Linking analysts' chat accounts to Switch would let the team verify who is asking and who owns the follow-up.
- The ALERT-1003 decline has no recorded reason. Giving the reason with the decision keeps the trail complete for the day shift.
