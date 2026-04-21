# thebardchat Discord — Love & Light Community

> **Try Claude free for 2 weeks** — the AI powering this entire ecosystem. [Start your free trial →](https://claude.ai/referral/4fAMYN9Ing)

---

[![Discord](https://img.shields.io/badge/Join-Discord-5865F2?style=for-the-badge&logo=discord)](https://discord.gg/thebardchat)
[![Twitch](https://img.shields.io/badge/Watch-Twitch-9146ff?style=for-the-badge&logo=twitch)](https://twitch.tv/thebardchat)
[![Built with Claude](https://img.shields.io/badge/Built%20With-Claude%20AI-orange?style=for-the-badge)](https://claude.ai/referral/4fAMYN9Ing)

The official Discord for **twitch.tv/thebardchat** — a family streaming community built on faith, sobriety, and love. No toxicity. No dark corners. Real people, real AI, real connection.

---

## Channel Structure

### 📋 Information
| Channel | Purpose |
|---------|---------|
| `#welcome` | First stop — rules, roles, how to get started |
| `#announcements` | Go-live alerts, stream schedule, big news |
| `#rules` | Community guidelines (see [CONSTITUTION.md](../CONSTITUTION.md)) |
| `#roles` | Self-assign roles to personalize your experience |

### 💬 Community
| Channel | Purpose |
|---------|---------|
| `#general` | Main hangout — anything goes (within rules) |
| `#stream-chat` | Live stream discussion overflow |
| `#gaming` | Gavin, Kai, Pierce, Jaxton, Ryker — all things games |
| `#introductions` | New? Tell us who you are |
| `#prayer-requests` | Faith and support — this is a safe space |

### 🤖 AI Corner
| Channel | Purpose |
|---------|---------|
| `#shanebrain` | Ask ShaneBrain anything — powered by local Ollama |
| `#ai-experiments` | Share what you're building or broke |
| `#mega-crew-logs` | MEGA Crew bot activity, highlights, funny moments |
| `#tech-talk` | Local AI, Pi 5, Raspberry Pi, homelab nerds welcome |

### 🎙️ Stream
| Channel | Purpose |
|---------|---------|
| `#clip-of-the-day` | Best clips from recent streams |
| `#schedule` | Weekly stream schedule + polls |
| `#suggestions` | What do you want to see on stream? |
| `#milestones` | Sobriety, follower goals, community wins |

### 🎵 Voice
| Channel | Purpose |
|---------|---------|
| `🔊 Stream Watch Party` | Watch together while Shane is live |
| `🔊 Gaming Lounge` | Chill gaming, open invite |
| `🔊 AFK Lounge` | Background company, no pressure to talk |

---

## Roles

| Role | How to Get It | What It Means |
|------|--------------|----------------|
| `🌟 Crew Member` | Auto on join | You're family now |
| `🎮 Gamer` | Self-assign in #roles | Gaming channels unlocked |
| `🤖 AI Nerd` | Self-assign in #roles | AI Corner channels |
| `🙏 Faith` | Self-assign in #roles | Prayer and support channels |
| `📻 Stream Rider` | Catch 5 streams | Loyal viewer, verified |
| `⚡ Regular` | Active community member | Mod discretion |
| `🛡️ Moderator` | Invited by Shane | Community guardian |
| `👑 The Crew` | Family only | Gavin, Kai, Pierce, Jaxton, Ryker |

---

## Bot Commands (in Discord)

| Command | What It Does |
|---------|-------------|
| `!shanebrain <question>` | Ask the local AI anything |
| `!sobriety` | Shane's sobriety counter (since 11/27/2023) |
| `!love` | Random love-and-light quote |
| `!schedule` | This week's stream schedule |
| `!clip` | Best clip from last stream |
| `!book` | Info on Shane's noir vignette book |

---

## Go-Live Alerts

When Shane goes live on Twitch, an N8N webhook fires automatically:
- `#announcements` gets a Discord embed with stream title, game, thumbnail
- Optional `@Stream Rider` ping (can be toggled in roles)
- Clip highlights posted to `#clip-of-the-day` via automated pipeline

See [`../n8n/twitch-go-live.json`](../n8n/twitch-go-live.json) for the workflow.

---

## Community Rules (Short Version)

1. Love and light — no exceptions
2. No hate, slurs, harassment, or dark energy
3. Keep it family-friendly
4. Respect sobriety — this channel is recovery-friendly
5. No unsolicited self-promotion
6. AI tools are welcome — disclose when using them
7. Mods have final say

Full rules in [CONSTITUTION.md](../CONSTITUTION.md).

---

## Structure Notes (for mods/bots)

- Go-live webhook → `#announcements` embed (N8N workflow)
- Clip pipeline → `#clip-of-the-day` auto-post
- ShaneBrain bot → routes to local Ollama cluster on Pi 5
- Sobriety counter → calculated from 2023-11-27 in real time
- All bot logic lives in [`../bot/bot.py`](../bot/bot.py)

---

*Built with [Claude](https://claude.ai/referral/4fAMYN9Ing) — try it free for 2 weeks.*
