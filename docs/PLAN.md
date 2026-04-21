# thebardchat Twitch — Autonomous Platform Build Plan

> *Authored by Shane Brazelton + Claude (Anthropic) | 2026-04-21*
> *Mission: Build a 1st-class, love-and-light family Twitch channel that runs itself when Shane is busy with life.*

---

## The Vision

A Twitch channel that:
- **Feels alive** — even when Shane isn't streaming, the community is active
- **Runs autonomously** — bots handle scheduling reminders, clip highlights, social posts, Discord pings
- **Serves the family** — any Brazelton can jump on and the tech handles the rest
- **Demonstrates AI** — live, honest demos of local AI — not black-box magic, real Pi 5 inference
- **Sheds love and light** — proactively counter-cultures against Twitch toxicity

---

## Phase 1 — Foundation (Week 1–2)

**Goal:** Channel is functional, bot is live, pages look good.

### 1A. Twitch Developer Setup
- [ ] Create Twitch Developer App at dev.twitch.tv
- [ ] Generate OAuth token with scopes: `chat:read chat:edit clips:edit channel:manage:broadcast`
- [ ] Store credentials in Weaviate vault (category: `twitch_credentials`)
- [ ] Test OAuth flow with curl — verify token is valid
- [ ] Register EventSub webhook for `stream.online` and `stream.offline` events

### 1B. Chat Bot (bot/bot.py)
- [ ] Install twitchio: `pip install twitchio --user --break-system-packages`
- [ ] Build BaseBot with twitchio.Client, reconnect handling, rate limiting
- [ ] Core commands: `!shanebrain`, `!love`, `!sobriety`, `!crew`, `!book`, `!discord`, `!clip`
- [ ] `!shanebrain` → POST to `http://localhost:8100/mcp` → ollama_generate → reply in chat
- [ ] `!sobriety` → calculate days since 11/27/2023, return formatted string
- [ ] `!love` → pull random quote from Weaviate LegacyKnowledge, tag `love`
- [ ] Deploy as systemd service `twitch-bot` on Pi 5
- [ ] Log every command call to Weaviate ExternalPerspectives collection

### 1C. Channel Setup (Twitch Dashboard)
- [ ] Write compelling channel bio (use CONSTITUTION.md pillars)
- [ ] Set up channel panels (About, Commands, Discord, AI Info)
- [ ] Add stream schedule (propose: Tue/Thu/Sat evenings, flexible)
- [ ] Upload brand graphics (from GitHub Pages art)
- [ ] Set default stream title template: "🤖 [TOPIC] — Love & Light | !shanebrain"
- [ ] Enable slow mode (3s) and subscriber-only for emotes
- [ ] Set AutoMod level 3 (aggressive — this is a family channel)

### 1D. GitHub Pages (index.html)
- [x] Beautiful schedule + about page deployed
- [ ] Enable GitHub Pages on repo (Settings → Pages → main branch root)
- [ ] Add custom OG meta tags for social sharing
- [ ] Link from Twitch channel panel

---

## Phase 2 — Automation (Week 3–4)

**Goal:** Stream events automatically trigger alerts and social posts.

### 2A. Go-Live Pipeline (N8N)
- [ ] Build N8N workflow: Twitch EventSub `stream.online` → Discord embed
  - Embed: Stream title, game, thumbnail, "Go Watch!" button
  - Ping @everyone in #stream-alerts channel
- [ ] Add Weaviate log entry on go-live (topic: stream start, title, game, timestamp)
- [ ] Optional: Auto-tweet/post to Facebook via existing social bot
- [ ] Export workflow to `n8n/twitch-go-live.json`

### 2B. Clip Highlight Pipeline
- [ ] N8N workflow: Every 30 min during stream → get top clips → post to Discord #clips
- [ ] End-of-stream: compile top 3 clips → create highlight reel post for Facebook
- [ ] `!clip` command → call Twitch Clips API → return clip URL in chat within 10 seconds
- [ ] Export workflow to `n8n/clip-highlight.json`

### 2C. OBS Overlays
- [ ] `alerts/go-live.html` — animated alert when someone follows/subscribes
  - Warm amber/purple gradient, "WELCOME [username]!" with custom animation
  - Audio: soft chime (no jump scare energy)
- [ ] `alerts/overlay.html` — persistent stream overlay
  - Bottom bar: ShaneBrain AI status (green = Ollama UP, yellow = degraded)
  - Top-right: sobriety day counter (live updating)
  - Bottom-right: !shanebrain prompt reminder

### 2D. Stream Schedule Bot
- [ ] Add `!schedule` command → pulls from a JSON file with weekly schedule
- [ ] N8N timer: every Tuesday at 5pm → Discord reminder "Stream in 3 hours!"
- [ ] Update schedule JSON via MEGA Dashboard or CLI (no manual edits)

---

## Phase 3 — AI Integration (Week 5–6)

**Goal:** The channel is visibly AI-powered in ways viewers can interact with.

### 3A. Live !shanebrain Enhancement
- [ ] Add conversation memory — !shanebrain remembers context within a stream session
- [ ] Route to cluster proxy (port 11435) for fastest response
- [ ] Model: llama3.1:8b from Pulsar00100 (fastest node) for snappy chat responses
- [ ] Add cooldown: 10 second per-user cooldown, 30 second global cooldown
- [ ] Response truncated at 400 chars for chat readability
- [ ] Add `!sb` as alias

### 3B. AI Stream Summary (End-of-Stream)
- [ ] On `stream.offline` event → trigger N8N workflow:
  1. Pull last stream's Weaviate logs (all !shanebrain queries, community moments)
  2. Send to Gemini/Claude → generate 300-word stream recap
  3. Post recap to Discord #stream-recaps
  4. Save recap to Weaviate DailyNote with tag `twitch`

### 3C. MEGA Crew Integration
- [ ] Wire Gemini Strategist to analyze stream performance data
  - Input: viewer count, chat rate, top commands used, clip count
  - Output: coaching note on content strategy stored in gemini_guidance.json
- [ ] Blaze bot: ingest stream recaps into Weaviate knowledge base
- [ ] Show "MEGA Crew Online" indicator on overlay when Pi services are healthy

### 3D. AI-Powered Raid Target Finder
- [ ] After stream ends: query Twitch API for live channels in similar categories
- [ ] Filter: positive community signal (no hate raids history), small/medium size
- [ ] Present top 3 raid candidates to Shane via Discord DM with one-click approve
- [ ] On approve: bot sends raid command to Twitch channel

---

## Phase 4 — Community (Week 7–8)

**Goal:** Viewers feel invested. The community has its own identity.

### 4A. Channel Points + Loyalty
- [ ] Create custom channel point rewards:
  - "Ask ShaneBrain" (100 pts) — priority !shanebrain queue, longer response
  - "Choose the Game" (5000 pts) — viewer nominates next game
  - "Meet the MEGA Crew" (500 pts) — bot introduces a random crew bot in chat
  - "Dad Joke" (200 pts) — Shane tells a dad joke on stream
- [ ] Log all redeems to Weaviate for analytics

### 4B. Discord Sync
- [ ] Discord bot commands that mirror Twitch:
  - `/shanebrain <question>` → same AI relay
  - `/stream` → current Twitch status (live/offline + title)
  - `/crew` → MEGA Crew status summary
- [ ] Auto-role assignment: Twitch subscribers → "Streamer" role in Discord
- [ ] Weekly digest: top moments, community highlights, posted Sunday

### 4C. Family Stream Nights
- [ ] Establish "Family Stream" template — any Brazelton can go live with one-click setup
  - Pre-configured stream key for family use
  - Auto-sets title format: "🎮 [NAME] is Live! Family Stream | thebardchat"
  - Bot auto-announces in Discord when family member goes live
- [ ] Create "guest streamer" Twitch account guide (for boys who want their own accounts)

### 4D. Community Goals
- [ ] Set visible community goals on stream:
  - "100 followers → Shane does a full AI build stream"
  - "250 followers → Family game night stream"
  - "500 followers → Live noir audiobook reading"
- [ ] Track via channel points milestone system

---

## Phase 5 — Autonomous Operation (Month 3+)

**Goal:** The channel maintains itself when life gets busy (Tiffany's health, work crunch, family needs).

### 5A. Self-Scheduling
- [ ] MEGA Crew Crank bot: analyze stream performance data → suggest optimal stream times
  - Input: historical viewer counts by time/day
  - Output: weekly schedule recommendation in Discord
- [ ] Auto-update Twitch schedule via API when Shane approves via Discord reaction
- [ ] Pre-stream checklist: N8N sends Shane a DM 30 min before scheduled stream
  - "Stream in 30 min: [title]. Services OK? Ollama UP? MEGA Crew active? Reply ✅ to auto-announce."

### 5B. Content Calendar AI
- [ ] Gemini Strategist generates weekly content ideas (Mon → full week plan):
  - Based on: current trends, Shane's Weaviate knowledge, recent stream performance
  - Format: 3 stream ideas with title, game/topic, AI demo angle, community hook
  - Posted to Discord #content-planning every Monday at 9 AM
- [ ] Shane approves/modifies via Discord reactions, bot updates schedule

### 5C. Highlight Reel Automation
- [ ] End-of-week: N8N pulls top 5 clips from past 7 days
- [ ] Generates a "Week in Review" post for Facebook + Discord
- [ ] MEGA Crew Storyteller: writes a narrative recap of the week's stream moments
- [ ] Auto-posts Sunday at 6 PM

### 5D. Crisis Mode
- [ ] If Shane marks himself "unavailable" (via MCP tool or Discord slash command):
  - Channel auto-posts "Taking a break — family first" Twitch status
  - Discord announcement: "Shane and fam need some time. Community keeps the light on."
  - Bot runs "community mode" — viewer-driven games, polls, AI chat
  - Resume announcement when Shane marks himself available

### 5E. Growth Analytics Dashboard
- [ ] New panel in Mega Dashboard: "Twitch Pulse"
  - Live viewer count (when streaming)
  - Follower growth chart (7/30/90 day)
  - Top clips this week
  - Community engagement score
  - Next scheduled stream countdown
- [ ] Daily Weaviate ingest: follower count, avg viewers, peak viewers, new clips

---

## Stream Content Ideas

### Recurring Shows
| Show | Cadence | Concept |
|------|---------|---------|
| **ShaneBrain Live** | Weekly | Build something with AI in real time — viewers suggest features |
| **Family Takeover** | Monthly | The boys run the stream — Dad just watches |
| **Love & Light Fridays** | Monthly | No gaming — honest conversation, community Q&A |
| **Noir Night** | Bi-weekly | Live audiobook reading from "You Probably Think This Book Is About You" |
| **Local AI School** | Monthly | Teach viewers to set up their own local AI — no cloud required |
| **The Pi Challenge** | Occasional | Can we build X entirely on a Raspberry Pi? Live attempt |

### One-Off Events
- **Sobriety Milestone Streams** — every 100 days sober, special stream
- **Book Announcement Streams** — when Vol 2 is ready
- **Charity Streams** — aligned with family values (family health, local community)
- **Collab Streams** — with creators who align with love-and-light mission
- **Angel Cloud Launch** — when the wellness platform goes live, stream the launch

---

## Success Metrics

| Milestone | Target | Reward Stream |
|-----------|--------|---------------|
| 100 followers | Month 1 | Full AI build stream |
| 250 followers | Month 2 | Family game night |
| 500 followers | Month 3 | Live noir reading |
| Affiliate | ~50 avg viewers | Community celebration stream |
| 1K followers | Month 6 | Shane's choice — whatever the community votes |

---

## Notes on Tone

This is not a hustle channel. We are not optimizing for algorithm-friendly content, clickbait thumbnails, or manufactured hype. We are building something genuine that we'd want to watch ourselves.

If growth is slow — that's fine. The community that finds this channel finds it because it's real.

> *"We're not trying to win Twitch. We're trying to make a corner of it worth being in."* — Shane Brazelton

---

*Built by Shane Brazelton + Claude (Anthropic) | [Try Claude free →](https://claude.ai/referral/4fAMYN9Ing)*
