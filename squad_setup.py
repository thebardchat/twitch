#!/usr/bin/env python3
"""squad_setup.py - Stream Squad opt-in role + reaction-sync for thebardchat.

Replaces the @everyone go-live ping with an opt-in @Stream Squad role.

Idempotent - safe to re-run and to put on cron:
  1. Ensures a mentionable "Stream Squad" role exists in the guild.
  2. Ensures an opt-in message exists in the opt-in channel, with a bell
     reaction the bot has added (members one-tap to join).
  3. Syncs membership: everyone who reacted gets the role; anyone who removed
     their reaction loses it (full reconcile). Bots skipped.
  4. Persists role/channel/message ids to stream_squad.json so golive.py can
     ping <@&ROLE_ID> instead of @everyone.

Run once AFTER the bot has Manage Roles in the guild, then drop on cron to keep
membership synced:
    */5 * * * * /usr/bin/python3 /home/shanebrain/twitch/squad_setup.py >> /var/log/shanebrain/squad.log 2>&1

Flags:
    --check      verify perms + report opt-in count, make NO changes
    --no-remove  grant roles but never strip them (additive only)

Blocker: needs ShaneBrainLegacyBot to have MANAGE_ROLES in guild
1103685980633972819 (thebardchat). Without it the script exits cleanly with a
diagnostic and changes nothing.
"""
import os, sys, json, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

GUILD_ID    = os.environ.get("DISCORD_SQUAD_GUILD", "1103685980633972819")   # thebardchat
OPTIN_CHAN  = os.environ.get("DISCORD_SQUAD_CHANNEL", "1103685981263110296") # default #announcements
ROLE_NAME   = os.environ.get("DISCORD_SQUAD_ROLE", "Stream Squad")
ROLE_COLOR  = int(os.environ.get("DISCORD_SQUAD_COLOR", str(0x9146FF)))      # Twitch purple
EMOJI       = "\U0001F514"                                                   # :bell:
TWITCH_URL  = os.environ.get("TWITCH_URL", "https://twitch.tv/thebardchat")
DISCORD_ENV = Path("/mnt/shanebrain-raid/shanebrain-core/bot/.env")
STATE_FILE  = Path(__file__).resolve().parent / "stream_squad.json"
UA  = "DiscordBot (https://shanebrain.cloud, 1.0)"
API = "https://discord.com/api/v10"

MANAGE_ROLES = 1 << 28
ADMIN        = 1 << 3

OPTIN_TEXT = (
    "**\U0001F514 Join the Stream Squad**\n"
    "React with \U0001F514 below to get pinged when **thebardchat** goes live on "
    f"Twitch - {TWITCH_URL}\n"
    "Remove your \U0001F514 anytime to stop the pings. (No more @everyone.)"
)


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
    headers = {"Authorization": "Bot " + TOKEN, "User-Agent": UA,
               "Content-Type": "application/json"}
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    for _ in range(5):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
                return json.loads(raw) if (expect_json and raw) else None
        except urllib.error.HTTPError as e:
            if e.code == 429:  # rate limited - honour Retry-After then retry
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


def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2))


def bot_perms_in_guild():
    for g in api("GET", "/users/@me/guilds"):
        if str(g["id"]) == str(GUILD_ID):
            return int(g.get("permissions", 0))
    return None


def ensure_role():
    for r in api("GET", f"/guilds/{GUILD_ID}/roles"):
        if r["name"] == ROLE_NAME:
            return r["id"], False
    created = api("POST", f"/guilds/{GUILD_ID}/roles",
                  {"name": ROLE_NAME, "color": ROLE_COLOR,
                   "mentionable": True, "hoist": False})
    return created["id"], True


def ensure_optin_message(state):
    mid = state.get("message_id")
    if mid:
        try:
            api("GET", f"/channels/{OPTIN_CHAN}/messages/{mid}")
            return mid, False
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    msg = api("POST", f"/channels/{OPTIN_CHAN}/messages", {"content": OPTIN_TEXT})
    emj = urllib.parse.quote(EMOJI)
    api("PUT", f"/channels/{OPTIN_CHAN}/messages/{msg['id']}/reactions/{emj}/@me",
        expect_json=False)
    return msg["id"], True


def reactors(message_id):
    emj = urllib.parse.quote(EMOJI)
    users, after = [], None
    while True:
        q = "?limit=100" + (f"&after={after}" if after else "")
        batch = api("GET",
                    f"/channels/{OPTIN_CHAN}/messages/{message_id}/reactions/{emj}{q}")
        if not batch:
            break
        users.extend(batch)
        if len(batch) < 100:
            break
        after = batch[-1]["id"]
    return [u["id"] for u in users if not u.get("bot")]


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


def sync(role_id, message_id, remove=True):
    want = set(reactors(message_id))
    have = role_members(role_id)
    added, removed = [], []
    for uid in want - have:
        api("PUT", f"/guilds/{GUILD_ID}/members/{uid}/roles/{role_id}", expect_json=False)
        added.append(uid)
    if remove:
        for uid in have - want:
            api("DELETE", f"/guilds/{GUILD_ID}/members/{uid}/roles/{role_id}",
                expect_json=False)
            removed.append(uid)
    return added, removed


def main():
    if not TOKEN:
        print("FATAL: no DISCORD_TOKEN in", DISCORD_ENV)
        sys.exit(2)
    check_only = "--check" in sys.argv
    no_remove  = "--no-remove" in sys.argv

    perms = bot_perms_in_guild()
    if perms is None:
        print(f"FATAL: bot is not in guild {GUILD_ID}")
        sys.exit(2)
    print(f"[perms] guild {GUILD_ID}: "
          f"MANAGE_ROLES={bool(perms & MANAGE_ROLES)} ADMIN={bool(perms & ADMIN)}")
    if not (perms & MANAGE_ROLES or perms & ADMIN):
        print("BLOCKED: bot lacks Manage Roles in this guild - grant it, then "
              "re-run. No changes made.")
        sys.exit(1)

    state = load_state()
    if check_only:
        print("[check] state:", json.dumps(state))
        if state.get("message_id"):
            print(f"[check] {len(reactors(state['message_id']))} member(s) opted in")
        sys.exit(0)

    role_id, role_new = ensure_role()
    print(f"[role] {ROLE_NAME} id={role_id} ({'created' if role_new else 'existing'})")

    message_id, msg_new = ensure_optin_message(state)
    print(f"[optin] message id={message_id} "
          f"({'posted' if msg_new else 'existing'}) in channel {OPTIN_CHAN}")

    state.update({"role_id": role_id, "guild_id": GUILD_ID,
                  "message_id": message_id, "channel_id": OPTIN_CHAN, "emoji": EMOJI})
    save_state(state)

    added, removed = sync(role_id, message_id, remove=not no_remove)
    print(f"[sync] +{len(added)} granted, -{len(removed)} removed")
    print(f"[done] golive.py can now ping <@&{role_id}>. state -> {STATE_FILE}")


if __name__ == "__main__":
    main()
