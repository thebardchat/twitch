#!/usr/bin/env python3
"""automod_setup.py - conservative Discord AutoMod for thebardchat (family server).

One-shot, idempotent: creates block-only AutoMod rules (NO auto-timeout / ban),
each of which blocks the offending message and posts an alert to #moderator-only
so a human can follow up. Re-running skips rules that already exist by name.

Rules:
  * "Mention spam"      - blocks messages with > 6 user/role mentions (raid/ping spam)
  * "Slurs & sexual"    - Discord's SLURS + SEXUAL_CONTENT keyword presets
  * "Profanity"         - Discord's PROFANITY preset (drop this one if too strict;
                          remove the rule in Server Settings -> AutoMod, or delete
                          by name and re-run)

Tune by editing RULES below and re-running. Needs the bot to have Manage Server
(it has admin).
"""
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

GUILD_ID = "1103685980633972819"
DISCORD_ENV = Path("/mnt/shanebrain-raid/shanebrain-core/bot/.env")
MOD_CHANNEL = "1370114312387170417"  # #moderator-only (alerts land here)
UA = "DiscordBot (https://shanebrain.cloud, 1.0)"
API = "https://discord.com/api/v10"

# AutoMod enums: event_type 1=MESSAGE_SEND; trigger 4=KEYWORD_PRESET 5=MENTION_SPAM
# presets: 1=PROFANITY 2=SEXUAL_CONTENT 3=SLURS ; actions: 1=BLOCK 2=ALERT
BLOCK = {"type": 1, "metadata": {"custom_message": "Blocked by AutoMod - let's keep it family-friendly \U0001F49B"}}
ALERT = {"type": 2, "metadata": {"channel_id": MOD_CHANNEL}}

# Discord allows only ONE rule of trigger_type 4 (KEYWORD_PRESET) and ONE of
# type 5 (MENTION_SPAM) per guild, so those are singletons we update in place.
SINGLETON_TYPES = {3, 4, 5}
RULES = [
    {"name": "Mention spam", "event_type": 1, "trigger_type": 5,
     "trigger_metadata": {"mention_total_limit": 6},
     "actions": [BLOCK, ALERT], "enabled": True},
    {"name": "Profanity, slurs & sexual", "event_type": 1, "trigger_type": 4,
     "trigger_metadata": {"presets": [1, 2, 3], "allow_list": []},
     "actions": [BLOCK, ALERT], "enabled": True},
]


def envget(path, key):
    for line in open(path):
        line = line.strip()
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


TOKEN = envget(DISCORD_ENV, "DISCORD_TOKEN")


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Authorization": "Bot " + TOKEN, "User-Agent": UA,
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, (json.loads(e.read() or b"null"))


def main():
    if not TOKEN:
        print("FATAL: no DISCORD_TOKEN"); sys.exit(2)
    dry = "--dry-run" in sys.argv

    base = f"/guilds/{GUILD_ID}/auto-moderation/rules"
    st, existing = api("GET", base)
    if st != 200:
        print(f"FATAL: cannot list rules [{st}]: {existing}"); sys.exit(1)
    by_type = {}
    for r in existing:
        by_type.setdefault(r["trigger_type"], []).append(r)
    by_name = {r["name"]: r for r in existing}
    print(f"[existing rules] {sorted(r['name'] for r in existing) or 'none'}")

    for rule in RULES:
        tt = rule["trigger_type"]
        # singleton types match by type (only one allowed); others match by name
        found = (by_type.get(tt) or [None])[0] if tt in SINGLETON_TYPES else by_name.get(rule["name"])
        patch = {k: rule[k] for k in ("name", "trigger_metadata", "actions", "enabled")}
        if found:
            if dry:
                print(f"[would update] '{found['name']}' -> {json.dumps(rule['trigger_metadata'])}")
                continue
            st, res = api("PATCH", f"{base}/{found['id']}", patch)
            print(f"[updated] '{rule['name']}' (id {found['id']}) [{st}]")
        else:
            if dry:
                print(f"[would create] {rule['name']} -> {json.dumps(rule['trigger_metadata'])}")
                continue
            st, res = api("POST", base, rule)
            print(f"[created] {rule['name']} (id {res.get('id')})" if st in (200, 201)
                  else f"[FAIL] {rule['name']} [{st}]: {res}")
    print("[done] alerts -> #moderator-only; block-only, no auto-timeout/ban.")


if __name__ == "__main__":
    main()
