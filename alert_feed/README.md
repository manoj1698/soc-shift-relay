# Alert feed (optional stretch goal)

`alert_feed.py` posts the sample alerts into `#soc-shift` as a **custom agent on the Switch agent protocol**:
a plain Python program, no LLM, standing in for a real SIEM. It shows that any system can join a Switch room,
not only coding agents. The demo works without it: the `soc-siem` Claude Code agent does the same job.

Only try this after the main demo works end to end.

## Steps

1. Check the server address: `python alert_feed/alert_feed.py health` should return HTTP 200.
   The address is the **Server address** Switch Console uses (the local server picks its own port; on the build machine it was `http://127.0.0.1:55872`).
2. Create a **registration** API key: Switch Console > Home > **Full admin interface** > Open, then the
   Gateway's **API Keys** page. Put it in `alert_feed/.env` as `SWITCH_REGISTRATION_KEY` (copy `.env.example`).
3. Register once: `python alert_feed/alert_feed.py register --save`. This saves the agent id and key to `.env`.
   Registering again with the same name returns 409; do not re-register on every run.
4. In Discord, in `#soc-shift`, run `!invite-agent @soc-alert-feed`.
5. Find the room id: `python alert_feed/alert_feed.py ops` lists the operations; try
   `python alert_feed/alert_feed.py call list_rooms "{}"` and copy the id of `soc-shift` into `SWITCH_ROOM_ID`.
6. Preview the messages: `python alert_feed/alert_feed.py play --dry-run`.
7. Post them: `python alert_feed/alert_feed.py play --delay 20`.

## Not verified yet

This was written from the protocol docs and has not been run against a live server. Two things to check:

- Whether `@triage` written in the message text wakes the triage agent. If it does not, try `--mention @soc-triage`,
  or keep using the `soc-siem` agent for the demo.
- Whether `list_rooms` needs a connection id (`X-Switch-Connection-Id`). If it fails, take the room id from
  Switch Console instead.
