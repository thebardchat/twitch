#!/usr/bin/env python3
"""follower_watch.py - celebrate Twitch follower milestones in Discord.

Polls the broadcaster's follower total (Helix /channels/followers via the
broadcaster user token) and, when it crosses a milestone, posts a celebration
to Discord. Edge-triggered via .follower_state.json so each milestone fires
exactly once. Built for cron */15.

  python3 follower_watch.py             # poll (cron)
  python3 follower_watch.py --dry-run   # read + decide, post nothing
  python3 follower_watch.py --test --dry-run  # render a sample celebration line
"""
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

HERE = Path("/home/shanebrain/twitch")
ENVF = HERE / ".env"
DISCORD_ENV = Path("/mnt/shanebrain-raid/shanebrain-core/bot/.env")
STATE = HERE / ".follower_state.json"
CELEBRATE_CHANNEL = os.environ.get("DISCORD_FOLLOWER_CHANNEL", "1103685981263110298")  # #general
TWITCH_URL = "https://twitch.tv/thebardchat"
MILESTONES = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]


def envget(path, key):
    if not path.exists():
        return None
    for ln in path.read_text(errors="ignore").splitlines():
        ln = ln.strip()
        if ln.startswith(key + "="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def get(url, hdr):
    req = urllib.request.Request(url, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except Exception:
            return e.code, None


def follower_total(cid, token):
    st, u = get("https://api.twitch.tv/helix/users",
                {"Client-Id": cid, "Authorization": f"Bearer {token}"})
    if st != 200 or not u.get("data"):
        return None, None
    bid = u["data"][0]["id"]
    name = u["data"][0]["display_name"]
    st, f = get(f"https://api.twitch.tv/helix/channels/followers?broadcaster_id={bid}",
                {"Client-Id": cid, "Authorization": f"Bearer {token}"})
    if st != 200:
        return None, name
    return f.get("total"), name


def discord_post(channel, content, dtoken):
    body = json.dumps({"content": content, "allowed_mentions": {"parse": []}}).encode()
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{channel}/messages", data=body, method="POST")
    for k, v in {"Authorization": f"Bot {dtoken}", "Content-Type": "application/json",
                 "User-Agent": "follower/1.0"}.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            print("posted ->", json.loads(r.read()).get("id"))
            return True
    except urllib.error.HTTPError as e:
        print("post failed", e.code, (e.read() or b"")[:200])
        return False


def main():
    dry = "--dry-run" in sys.argv
    cid = envget(ENVF, "TWITCH_CLIENT_ID")
    tok = (envget(ENVF, "TWITCH_OAUTH_TOKEN") or "").replace("oauth:", "")
    dtoken = envget(DISCORD_ENV, "DISCORD_TOKEN")
    if not (cid and tok):
        raise SystemExit("missing TWITCH_CLIENT_ID / TWITCH_OAUTH_TOKEN in twitch/.env")

    total, name = follower_total(cid, tok)
    if total is None:
        raise SystemExit("could not read follower total (token scope/expiry?)")

    state = json.loads(STATE.read_text()) if STATE.exists() else {"celebrated": 0, "last_total": 0}
    celebrated = state.get("celebrated", 0)
    crossed = [m for m in MILESTONES if celebrated < m <= total]
    print(f"followers={total} celebrated<={celebrated} crossed={crossed}")

    if "--test" in sys.argv and not crossed:
        crossed = [total]  # render a sample line for the current count

    target = max(crossed) if crossed else None
    if target:
        msg = (f"\U0001F389 **{target} followers!** thebardchat just hit **{total}** on "
               f"Twitch \U0001F49C\nCome hang out - {TWITCH_URL}")
        if dry:
            print("[would post]", msg)
        elif discord_post(CELEBRATE_CHANNEL, msg, dtoken):
            state["celebrated"] = max(celebrated, target)

    state["last_total"] = total
    if not dry:
        STATE.write_text(json.dumps(state))


if __name__ == "__main__":
    main()
