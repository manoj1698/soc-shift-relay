# Setup on Windows with Discord

About 60 to 90 minutes the first time. You need two Discord accounts: yours (Analyst A and on-call) and a
second one (the employee and Analyst B). Switch Console for Windows is early access, so expect rough edges.

This guide uses Discord and Claude Code. On Slack, Microsoft Teams, Mattermost or Telegram, connect the app with
[Switch's guide for it](https://docs.switchagents.ai/switch-rooms/deploy/messaging-apps/index.md) in place of the
Discord steps; the rest is the same. For another AI agent (Codex, Cursor, OpenCode, Antigravity), see
[Other chat apps and AI agents](../README.md#other-chat-apps-and-ai-agents).

## 0. Get the repo and check your tools (5 min)

Open **Git Bash** (Claude Code on Windows runs commands through it), then:

```
git clone https://github.com/manoj1698/soc-shift-relay.git
cd soc-shift-relay
pwd -W               # the full path of your clone: step 4 asks for it
python --version     # 3.8 or newer. If it fails, try: py --version
claude --version     # Claude Code installed
claude               # sign in once if asked, then exit
```

If only `py` works, add Python to PATH: the agents' briefs run `python`.

Then, still in the repo folder:

```
python tools/install_agent_settings.py --trust
python -m unittest discover -s tests -v
python tools/reset_demo.py
```

The first command installs each agent's Claude Code permission rules (`workspaces/<agent>/.claude/settings.json`)
and marks the five agent folders as trusted in Claude Code's config (`~/.claude.json`, backed up first as
`.claude.json.bak-soc-shift-relay`). Claude Code ignores a folder's allow rules until the folder is trusted, and
Switch starts agents without the trust dialog: skip `--trust` and every harmless status check asks on-call for
approval. Prefer the dialog? Run `claude` once in each `workspaces\<agent>` folder, accept it, then `/exit`.
All tests should pass.

## 1. Install Switch Console (10 min)

1. Download the Windows installer: <https://github.com/sandbox-quantum/switch/releases/latest/download/switch-console-x64.exe>
2. Run it, open Switch Console, select **Get started**.
3. Under **How do you want to run Switch?** choose **On this computer**, select **Start** on
   **Set up a server on this computer**, wait until it says the server is running, then **Continue**.
4. Under **How'd you like to power switch-buddy?** choose Claude Code under **Already signed in**.
5. Reply to switch-buddy's welcome message with a small task (for example "draft a 3-line agenda") to prove an
   agent runs. Approve its permission request if it asks.

Docker: Switch's docs say the local server runs on Docker, but on our Windows machine it ran without Docker
running. If Switch Console asks for Docker, install Docker Desktop, start it, and try again.

## 2. Create the Discord server and bot (15 min)

1. In Discord, create a server, for example **SOC Demo**. Invite your second account.
2. Open the [Discord Developer Portal](https://discord.com/developers/applications), **New Application**, name it
   **Agent Switch**.
3. **Bot** tab: copy the **token** (reset it if hidden) and keep it private. Under **Privileged Gateway Intents**
   turn on **Server Members Intent** and **Message Content Intent**, then **Save Changes**.
   Without Message Content Intent the agents receive empty messages.
4. **OAuth2 > URL Generator**: scopes **bot** and **applications.commands**. Bot permissions: View Channels,
   Send Messages, Send Messages in Threads, Manage Webhooks, Manage Channels, Manage Roles, Read Message History,
   Attach Files, Add Reactions. Open the generated URL and add the bot to **SOC Demo**.
5. Discord **User Settings > Advanced** (or Developer): turn on **Developer Mode**. Right-click the server icon,
   **Copy Server ID**. Switch calls this the **Guild Id**.

## 3. Connect Discord to Switch (5 min)

1. Switch Console sidebar: your server's **Home** page > **Messaging apps** > **Connect** > **Discord**.
2. **Name**: `SOC Demo`. Paste the **Bot Token** and the **Guild Id**. Leave **Agent name autocomplete** on.
   Select **Connect**.
3. Link your account: search for yourself and select **This is me**. The template puts you in the rooms through
   this link, so do not skip it.

## 4. Import and run the template (10 min)

1. Switch Console > **Templates** > **Import template** > **Choose file** > `switch\soc-shift-relay.template.yaml`.
   Errors and notes show under the editor; fix every line they name first. Select **Import**, name it (for
   example SOC Shift Relay) and **Save**.
2. On the template's page select **Use template** and check the form:
   - **Name prefix**: `soc` (agents become soc-triage, soc-responder, soc-scribe, soc-appsec, soc-siem)
   - **Project folder**: the full path of your clone, with forward slashes (what `pwd -W` printed in step 0).
     The default is the author's folder, so change it.
   - **Messaging app**: the connection from step 3 (`SOC Demo`)
   - Advanced: **Runs on** this computer. There is no provider field: the template sets Claude Code for every
     agent, because the agents' safety rules are Claude Code settings (and Switch Console on Windows cannot fill
     a provider field in a template)
3. Select **Create all**. Expect five agents, a group with **#soc-shift** and **#security-help** linked
   together, the four roles, the **runbook** document, and a kickoff message in each room. Switch creates both
   Discord channels; do not make them yourself first.
4. Keep Switch Console open. The agents only answer while it runs.

If the run stops with an error, read the reason it names (for example a missing provider) and fix that first.
After 30 minutes of trouble, use the manual setup below.

## 5. Check everything (10 min)

In **#soc-shift** in Discord:

```
!list-agents        -> soc-triage, soc-responder, soc-scribe, soc-appsec, soc-siem
!roles              -> triage, responder, scribe, appsec, each with a holder
!list-documents     -> runbook, shift-log and on-call-roster
!agents-status      -> all five present
```

In **#security-help**, make triage the main agent so employees do not need to type @. A main agent needs
follow-ups, so check those first:

```
!follow-ups                 -> should say on; if it says off: !follow-ups on
!assign-agent @soc-triage
```

If `!follow-ups` is not available, the server has follow-ups turned off: employees then write `@soc-triage`.

If a job has no holder, ask: `@soc-triage take the triage job` (same for responder, scribe and appsec).
If shift-log or on-call-roster is missing: `@soc-scribe create the shift-log and on-call-roster room documents
from your brief`.

On each agent's page in Switch Console (**Your Agents**):

| Agent | Who can talk to your agent | Auto mode | Bypass permissions |
| --- | --- | --- | --- |
| soc-triage | Anyone | on | off |
| soc-responder | Me and my agents | **off** | **off** |
| soc-scribe | Anyone | on | off |
| soc-appsec | Me and my agents | on | off |
| soc-siem | Only me | on | off |

The template sets these; check them anyway, because @responder must always ask before it acts. Also keep
**Service access** off for every agent (Connectors, or the plug icon on the agent's page): the lab needs no
outside service, and a service you turn on lets the agent's sessions use your connection to it.

## 6. Rehearse

```
python tools/reset_demo.py
```

Then follow [docs/DEMO_SCRIPT.md](DEMO_SCRIPT.md). Before each new run, reset the lab and either use fresh channels or tell
@scribe "start a new shift log section for this run".

## Manual setup (only if the template fails)

The same sources work by hand:

1. **Your Agents > +** for each agent: Name `soc-triage` (then `soc-responder`, `soc-scribe`, `soc-appsec`,
   `soc-siem`),
   a one-line Description, **Agent instructions** = paste that agent's `workspaces/<agent>/AGENT.md`,
   **Run location** This computer, **Directory** = `<your clone>\workspaces\<agent>` (for soc-siem the folder
   is `workspaces\alert-sim`), **Agent provider** Claude Code. Then set the table in step 5.
2. **Your Rooms > Create room** > Discord: name `soc-shift`, Instructions = paste `switch/room-soc-shift.md`.
   Add the five agents. Repeat for `security-help` with `switch/room-security-help.md` and only soc-triage.
3. In #soc-shift: ask `@soc-scribe` to create a room document named `runbook` with the content of
   `switch/runbook.md` (paste it), then the shift-log and on-call-roster documents.
4. Ask an agent to define the four jobs from `switch/roles.md` (triage shared; responder, scribe and appsec
   exclusive), then ask each agent to take its job. Check with `!roles`.
5. Optional: ask an agent to link #security-help to #soc-shift with the label "escalates to the SOC desk" (the
   template does this for you; a link only tells agents the other room exists).

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Agent never answers | Switch Console must be open; address the exact name; check `!agents-status` |
| "CLI not installed" for Claude Code | On **Settings > Agent providers** select the refresh icon; if it still says so, quit Switch Console fully and reopen it (it reads PATH at startup) |
| "Session did not start" | A trust prompt is waiting in the provider's terminal; answer it, or turn on Settings > General > Auto-trust worktree directories |
| Agents get empty messages | Turn on Message Content Intent for the bot, save, restart the connection |
| No slash commands | Re-invite the bot with the applications.commands scope; the `!` commands always work |
| `@triage` does not reach the job holder | Address the agent by name instead (`@soc-triage`) |
| Agent keeps asking permission for harmless reads | Fine for @responder; for others turn Auto mode on |
| All rooms stop responding after a network change | Restart Switch Console |

Help: the Switch docs <https://docs.switchagents.ai/switch-rooms/resources/troubleshooting>.
