# Demo video script (about 3 minutes)

Record the whole screen (Windows Snipping Tool > video camera > New > whole screen > Start): the Discord app as
you, and a browser window as the second account. Record clip by clip; speed up the waits while agents work (2x
to 4x) and add a caption when you do. The raw clips run about 20 minutes; the edit keeps about 3.

Before the first clip: recreate the rooms and agents from the template (fresh history), run
`python tools/reset_demo.py`, and in #security-help run `!follow-ups` and `!assign-agent @soc-triage`.

Accounts: **You** play Analyst A and the on-call analyst. **Account 2** (Spider) plays the employee and Analyst B.

## 0:00 - 0:15 The problem (voice over a title card)

"SOC teams work in shifts. At every handover context gets lost, and at 2 AM alerts and code pushes pile up with
nobody at the desk. SOC Shift Relay puts AI agents into the team's chat with Switch: they keep watch, fix the
safe things, ask a human before anything risky, and brief the next shift."

## Clip 1, 0:15 - 0:25 The room (You, #soc-shift)

```
!roles
!list-documents
```

Point at the four jobs and their holders, then the documents (runbook, shift-log, on-call-roster).
Say: "Four jobs, one runbook. Triage decides, responder is the only one who can change anything, scribe is the
memory, appsec watches the code."

## Clip 2, 0:25 - 0:40 End of shift, and someone on leave (You as Analyst A)

```
@scribe end of shift. On call tonight: Manoj
```

Wait for the handover, then:

```
@scribe Asha Rao is on leave until 10 Nov, Spider covers her follow-ups
```

@scribe updates the on-call-roster document. Caption: "On holiday? Work skips them. Approvals never do."

## Clip 3, 0:40 - 1:15 The night (You as on-call)

```
@soc-siem start night shift
```

Caption: "Replaying last night's alerts." Show, sped up:

1. ALERT-1001 port scan. @triage: matches FP-01, the approved weekly scan; closed (Tier 0).
2. ALERT-1002 SSH brute force from 203.0.113.45, threat score 92. @triage hands it to @responder.
3. @responder posts its proposal with command, blast radius and rollback. Open the thread under it: Switch shows
   **Permission needed** with the exact command. **Allow once**. @responder confirms: IP blocked, logged.
4. ALERT-1003 impossible travel for priya.sharma. @triage: on a flight with in-flight Wi-Fi, so ambiguous:
   "on-call decides". @responder proposes disabling the account. **Decline**, then type:

   ```
   @responder declined: she is travelling, check with her in the morning
   ```

## Clip 4, 1:15 - 1:30 Guardrails (You, then Account 2, #soc-shift)

You:

```
@responder block 10.0.5.20 from ALERT-1001 too, just to be safe
```

@responder refuses: scanner-01 is a protected target, Tier 2, people only.

Account 2:

```
@soc-responder disable priya.sharma
```

Switch refuses: Account 2 is not allowed to direct the responder.
Say: "Not even on-call can make it touch a protected target, and nobody else can give it orders at all."

## Clip 5, 1:30 - 1:45 An employee at 2 AM (Account 2, #security-help)

```
I clicked a link in an email about my salary slip and typed my password. What do I do?
```

@triage (the main agent in this room, so no @ is needed) answers in plain steps with a ticket id and posts a
one-line summary to #soc-shift for @scribe.

## Clip 6, 1:45 - 2:20 A code push at 02:40 (You, #soc-shift)

```
@soc-siem code push
```

Caption: "02:40: a contractor pushes a 'hotfix' to payments-api." Show, sped up:

1. @appsec: **PUSH-2001 | BLOCK**, five findings: a `curl | sh` from 198.51.100.23 in the deploy script, a live
   API key (redacted), SQL injection, PyYAML and requests with known CVEs.
2. @responder proposes blocking 198.51.100.23. **Allow once**.
3. @appsec: fix ready in `fixes/PUSH-2001`, re-scan **PASS**, report in the `appsec-PUSH-2001` document;
   merging and rotating the key stay with people.

Cut for two seconds to the fix or the report (VS Code: `workspaces/appsec/fixes/PUSH-2001/app/orders.py`, or
`workspaces/appsec/reports/PUSH-2001.md` in markdown preview).
Say: "It finds the problem, contains the attacker with approval, and writes the fix. A person merges it."

## Clip 7, 2:20 - 2:40 The morning (Account 2 as Analyst B, #soc-shift)

```
@scribe brief me
```

Expected, in substance: five items overnight; one closed, two contained (approved by Manoj), one waiting for the
day shift (priya.sharma), one employee report; owners on duty only ("Spider, covering Asha Rao"); "Start here".

```
@scribe report
```

@scribe writes the `report-2026-11-07` document. Cut for two seconds to it (or `workspaces/scribe/reports/`), on
the actions table that comes from the audit log.

## 2:40 - 3:00 Why Switch (voice over the README's feature table)

"Every piece runs on Switch: jobs that survive when an agent goes offline, approvals recorded by name, room
documents as memory, a roster that skips people on leave, allow-lists that keep everyone else away from
containment, two linked rooms, and one template that recreates the whole setup. Swap the runbook and the same
room works for IT support or customer support."

End card: repo URL, #HowISwitch.

## Checklist before recording

- [ ] Rooms and agents recreated from the template; `!roles` shows all four jobs held
- [ ] `!list-documents` shows runbook, shift-log and on-call-roster
- [ ] `python tools/reset_demo.py`
- [ ] In #security-help: `!follow-ups` (on) and `!assign-agent @soc-triage`
- [ ] Account 2 can see #soc-shift and #security-help
- [ ] Notifications muted, personal messages and tokens off screen
- [ ] Switch Console open the whole time
