# CLAUDE.md — thebardchat Twitch Repo

> Project-level instructions for Claude Code sessions in this repo.
> Part of the ShaneBrain ecosystem at twitch.tv/thebardchat.
> Global instructions live at `/home/shanebrain/.claude/projects/-home-shanebrain/CLAUDE.md`

---

## What This Repo Is

The Twitch automation, bot, overlays, and GitHub Pages home for the thebardchat Twitch channel. A family streaming platform powered by the ShaneBrain local AI ecosystem (Pi 5, Ollama cluster, Weaviate, MEGA Crew bots, MCP server).

**Live channel:** twitch.tv/thebardchat
**Schedule page:** thebardchat.github.io/twitch/
**Discord:** linked from index.html

---

## Core Files

| File | Purpose |
|------|---------|
| `index.html` | GitHub Pages — stream schedule, about, social |
| `CONSTITUTION.md` | Channel values and rules |
| `bot/bot.py` | Twitch chat bot (twitchio Python) |
| `bot/commands.py` | Chat commands — !shanebrain, !love, etc. |
| `alerts/go-live.html` | Discord go-live alert trigger |
| `alerts/overlay.html` | OBS browser source overlay |
| `n8n/` | N8N workflow JSON exports |
| `docs/PLAN.md` | Full autonomous build plan |
| `docs/setup.md` | Twitch Developer App + OAuth setup |
| `docs/commands.md` | Full command reference |

---

## Environment Variables

Stored in Weaviate vault — do NOT hardcode these:

```
TWITCH_CLIENT_ID
TWITCH_CLIENT_SECRET
TWITCH_OAUTH_TOKEN
TWITCH_CHANNEL=thebardchat
SHANEBRAIN_MCP_URL=http://localhost:8100/mcp
SHANEBRAIN_OLLAMA_URL=http://localhost:11435
DISCORD_WEBHOOK_URL
```

Retrieve with: `scripts/env_from_vault.py` in shanebrain-core.

---

## Bot Architecture

- **Language:** Python (twitchio) — matches the rest of ShaneBrain's Python stack
- **AI relay:** `!shanebrain` → HTTP to MCP server `/invoke` → Ollama cluster → response in chat
- **Logging:** Every command invocation → Weaviate ExternalPerspectives collection
- **Runs as:** systemd service `twitch-bot` on Pi 5 (when built)
- **Port:** No HTTP port needed — outbound WebSocket to Twitch IRC only

---

## Rules For Claude

- **Voice of the channel:** Warm, family-friendly, love-and-light. Not corporate. Not gamer-edgy.
- **Referral banner:** Every time README is updated, keep the Claude referral banner at top
- **Referral link:** `https://claude.ai/referral/4fAMYN9Ing`
- **Credit:** Always `Built by Shane Brazelton + Claude (Anthropic)` — never "one guy built this"
- **Family sensitivity:** Boys (Gavin, Kai, Pierce, Jaxton, Ryker) are family members — never put them in UI by full name without Shane approving. Ryker is 5 — no photo of him ever.
- **Don't break global CLAUDE.md rules** — this file extends, not overrides
- **Twitch API limits:** Be aware of rate limits (800 joins/15min, 100 messages/30sec)
- **OBS overlays:** Keep browser sources at 1920x1080, transparent background
- **No dark patterns:** No fake viewer count, no misleading clips, no purchased followers

---

## Testing

- Bot commands: test with a private Twitch test channel before deploying to thebardchat
- Overlays: open in browser at 1920x1080 before loading in OBS
- N8N workflows: test with webhook.site before wiring live webhook

---

## Deployment

```bash
# Deploy bot to Pi 5 (when ready)
sudo cp bot/twitch-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now twitch-bot

# Update GitHub Pages
git add index.html && git commit -m "update: stream page" && git push
# GitHub Pages auto-deploys from main branch root
```

---

## Session Start Checklist

1. `shanebrain_system_health` — verify Pi services are up
2. `shanebrain_vault_search` with "twitch" — retrieve credentials
3. Check `docs/PLAN.md` for current phase and next steps
4. Check recent Twitch API changes at dev.twitch.tv/docs

---

*Built with [Claude](https://claude.ai/referral/4fAMYN9Ing) — try it free for 2 weeks.*
