# Twitch Bot Setup Guide

## Step 1 — Twitch Developer App

1. Go to [dev.twitch.tv/console](https://dev.twitch.tv/console)
2. Click **Register Your Application**
3. Name: `ShaneBrain Twitch Bot`
4. OAuth Redirect URL: `http://localhost`
5. Category: `Chat Bot`
6. Click **Create** → copy **Client ID** and **Client Secret**

## Step 2 — OAuth Token

Generate a token with the required scopes:

```bash
# Required scopes: chat:read chat:edit clips:edit channel:manage:broadcast
# Use the Twitch CLI or this URL (replace CLIENT_ID):
https://id.twitch.tv/oauth2/authorize
  ?response_type=token
  &client_id=YOUR_CLIENT_ID
  &redirect_uri=http://localhost
  &scope=chat:read+chat:edit+clips:edit+channel:manage:broadcast
```

Copy the `access_token` from the redirect URL. Prefix with `oauth:` for twitchio.

## Step 3 — Store in Weaviate Vault

```bash
# On Pi 5:
python3 scripts/env_from_vault.py --add TWITCH_CLIENT_ID=your_id
python3 scripts/env_from_vault.py --add TWITCH_CLIENT_SECRET=your_secret
python3 scripts/env_from_vault.py --add TWITCH_OAUTH_TOKEN=oauth:your_token
python3 scripts/env_from_vault.py --add TWITCH_CHANNEL=thebardchat
python3 scripts/env_from_vault.py --add DISCORD_WEBHOOK_URL=your_webhook
```

## Step 4 — Install Dependencies

```bash
pip install twitchio aiohttp --user --break-system-packages
```

## Step 5 — Deploy as Systemd Service

```ini
# /etc/systemd/system/twitch-bot.service
[Unit]
Description=thebardchat Twitch Bot
After=network.target ollama.service

[Service]
User=shanebrain
WorkingDirectory=/home/shanebrain/twitch/bot
EnvironmentFile=/home/shanebrain/twitch/.env
ExecStart=/usr/bin/python3 /home/shanebrain/twitch/bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now twitch-bot
sudo systemctl status twitch-bot
```

## Step 6 — EventSub Webhooks (Phase 2)

Register go-live webhook via Twitch CLI or curl:

```bash
curl -X POST https://api.twitch.tv/helix/eventsub/subscriptions \
  -H "Client-ID: $TWITCH_CLIENT_ID" \
  -H "Authorization: Bearer $TWITCH_OAUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "stream.online",
    "version": "1",
    "condition": {"broadcaster_user_id": "YOUR_USER_ID"},
    "transport": {
      "method": "webhook",
      "callback": "https://shanebrain-1.tail202c1a.ts.net/twitch/webhook",
      "secret": "your_webhook_secret"
    }
  }'
```

Get your user ID: `GET https://api.twitch.tv/helix/users?login=thebardchat`

## Environment File Template

```bash
# /home/shanebrain/twitch/.env
TWITCH_OAUTH_TOKEN=oauth:your_token
TWITCH_CHANNEL=thebardchat
SHANEBRAIN_MCP_URL=http://localhost:8100/mcp
SHANEBRAIN_OLLAMA_URL=http://localhost:11435
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```
