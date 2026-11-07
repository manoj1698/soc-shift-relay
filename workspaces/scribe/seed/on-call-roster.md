# On-call roster

Week of 2 to 8 Nov 2026 (IST). Tell @scribe in #soc-shift when someone is away or back, for example
"@scribe Asha Rao is on leave until 10 Nov, Spider covers her". @scribe keeps this document.

| Person | Role | Shift (IST) | Status | Cover while away |
| --- | --- | --- | --- | --- |
| Manoj | Night analyst, on call | 23:00 - 09:00 | on duty | - |
| Asha Rao | SOC lead, owns day-shift follow-ups | 09:00 - 18:00 | on duty | - |
| Spider | Day analyst | 09:00 - 18:00 | on duty | - |
| Neha Kapoor | payments-api lead (developer) | 10:00 - 19:00 | on duty | - |

Escalation order when a person must decide: on call, then SOC lead, then day analyst.

## Rules

- Before naming an owner or asking someone to decide, check their status. If they are away, use their cover;
  with no cover, the next person in the escalation order. Say who was skipped and why.
- Absence never approves. A Tier 1 action still needs Allow once from the on-call analyst in Switch. If nobody
  who can approve is on duty, the action waits and goes first in the next brief.
- Code findings that need a developer (merge a fix, rotate a key) go to the repository's lead.
