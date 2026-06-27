#!/usr/bin/env python3
"""roles.py - self-serve reaction-roles for thebardchat.

Idempotent (safe to re-run / cron): ensures each opt-in role exists, ensures a
#roles channel holding ONE embed that lists them, adds each emoji reaction, and
reaction-syncs membership (REST + cron, no gateway). Edit ROLE_SPECS to add or
remove roles. Separate from Stream Squad (squad_setup.py). Cron */5.

  python3 roles.py            # ensure + sync (cron)
  python3 roles.py --check    # report perms + state, no changes
  python3 roles.py --no-remove # additive only
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

GUILD_ID = os.environ.get("DISCORD_GUILD", "1103685980633972819")
DISCORD_ENV = Path("/mnt/shanebrain-raid/shanebrain-core/bot/.env")
STATE_FILE = Path(__file__).resolve().parent / "roles_state.json"
CHANNEL_NAME = os.environ.get("DISCORD_ROLES_CHANNEL_NAME", "roles")
UA = "DiscordBot (https://shanebrain.cloud, 1.0)"
API = "https://discord.com/api/v10"
MANAGE_ROLES = 1 << 28
ADMIN = 1 << 3

# --- edit this list to add / remove self-serve roles ---
ROLE_SPECS = [
    {"name": "Game Night",    "emoji": "\U0001F3AE", "color": 0x57F287},  # 🎮
    {"name": "Announcements", "emoji": "\U0001F4E3", "color": 0xFEE75C},  # 📣
    {"name": "Notify Me",     "emoji": "\U0001F4EC", "color": 0x5865F2},  # 📬
]


def envget(path, key):
    try:
        for line in open(path):
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        return None
    return None


TOKEN = envget(DISCORD_ENV, "DISCORD_TOKEN")


def api(method, path, body=None, expect_json=True):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Authorization": "Bot " + TOKEN, "User-Agent": UA,
                                          "Content-Type": "application/json"})
    for _ in range(5):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
                return json.loads(raw) if (expect_json and raw) else None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After", "1")) + 0.5)
                continue
            raise
    raise RuntimeError("rate-limit retries exhausted: " + path)


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def bot_perms():
    for g in api("GET", "/users/@me/guilds"):
        if str(g["id"]) == str(GUILD_ID):
            return int(g.get("permissions", 0))
    return None


def ensure_role(spec):
    for r in api("GET", f"/guilds/{GUILD_ID}/roles"):
        if r["name"] == spec["name"]:
            return r["id"]
    created = api("POST", f"/guilds/{GUILD_ID}/roles",
                  {"name": spec["name"], "color": spec["color"],
                   "mentionable": True, "hoist": False})
    return created["id"]


def ensure_channel(state):
    cid = state.get("channel_id")
    if cid:
        try:
            api("GET", f"/channels/{cid}")
            return cid, False
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    ch = api("POST", f"/guilds/{GUILD_ID}/channels",
             {"name": CHANNEL_NAME, "type": 0,
              "topic": "React to grab a role. Remove the reaction to drop it."})
    return ch["id"], True


def build_embed(specs):
    lines = [f"{s['emoji']}  **{s['name']}**" for s in specs]
    return {"title": "\U0001F3F7️ Pick your roles",
            "color": 0x5865F2,
            "description": "React below to opt into a role. Remove the reaction to "
                           "drop it.\n\n" + "\n".join(lines)}


def ensure_message(channel_id, specs, state):
    emojis = [s["emoji"] for s in specs]
    embed = build_embed(specs)
    mid = state.get("message_id")
    if mid:
        try:
            api("GET", f"/channels/{channel_id}/messages/{mid}")
            api("PATCH", f"/channels/{channel_id}/messages/{mid}",
                {"content": "", "embeds": [embed]})
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            mid = None
    if not mid:
        msg = api("POST", f"/channels/{channel_id}/messages", {"embeds": [embed]})
        mid = msg["id"]
    for e in emojis:
        api("PUT", f"/channels/{channel_id}/messages/{mid}/reactions/{urllib.parse.quote(e)}/@me",
            expect_json=False)
    return mid


def reactors(channel_id, message_id, emoji):
    emj = urllib.parse.quote(emoji)
    users, after = [], None
    while True:
        q = "?limit=100" + (f"&after={after}" if after else "")
        batch = api("GET", f"/channels/{channel_id}/messages/{message_id}/reactions/{emj}{q}")
        if not batch:
            break
        users.extend(batch)
        if len(batch) < 100:
            break
        after = batch[-1]["id"]
    return {u["id"] for u in users if not u.get("bot")}


def role_members(role_id):
    members, after = set(), "0"
    while True:
        batch = api("GET", f"/guilds/{GUILD_ID}/members?limit=1000&after={after}")
        if not batch:
            break
        for m in batch:
            if role_id in m.get("roles", []) and not m["user"].get("bot"):
                members.add(m["user"]["id"])
        if len(batch) < 1000:
            break
        after = batch[-1]["user"]["id"]
    return members


def sync(role_id, channel_id, message_id, emoji, remove=True):
    want = reactors(channel_id, message_id, emoji)
    have = role_members(role_id)
    added = removed = 0
    for uid in want - have:
        api("PUT", f"/guilds/{GUILD_ID}/members/{uid}/roles/{role_id}", expect_json=False)
        added += 1
    if remove:
        for uid in have - want:
            api("DELETE", f"/guilds/{GUILD_ID}/members/{uid}/roles/{role_id}", expect_json=False)
            removed += 1
    return added, removed


def main():
    if not TOKEN:
        print("FATAL: no DISCORD_TOKEN"); sys.exit(2)
    no_remove = "--no-remove" in sys.argv

    perms = bot_perms()
    if perms is None:
        print(f"FATAL: bot not in guild {GUILD_ID}"); sys.exit(2)
    print(f"[perms] MANAGE_ROLES={bool(perms & MANAGE_ROLES)} ADMIN={bool(perms & ADMIN)}")
    if not (perms & MANAGE_ROLES or perms & ADMIN):
        print("BLOCKED: bot lacks Manage Roles. No changes."); sys.exit(1)

    state = load_state()
    if "--check" in sys.argv:
        print("[check] state:", json.dumps(state)); sys.exit(0)

    specs = []
    for s in ROLE_SPECS:
        rid = ensure_role(s)
        specs.append({**s, "role_id": rid})
        print(f"[role] {s['name']} -> {rid}")

    channel_id, chan_new = ensure_channel(state)
    print(f"[channel] #{CHANNEL_NAME} {channel_id} ({'created' if chan_new else 'existing'})")
    message_id = ensure_message(channel_id, specs, state)
    print(f"[message] {message_id}")

    state.update({"channel_id": channel_id, "message_id": message_id,
                  "roles": {s["name"]: s["role_id"] for s in specs}})
    STATE_FILE.write_text(json.dumps(state, indent=2))

    tot_a = tot_r = 0
    for s in specs:
        a, r = sync(s["role_id"], channel_id, message_id, s["emoji"], remove=not no_remove)
        tot_a += a
        tot_r += r
    print(f"[sync] +{tot_a} granted, -{tot_r} removed across {len(specs)} roles")
    print("[done]")


if __name__ == "__main__":
    main()
