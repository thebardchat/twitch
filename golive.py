#!/usr/bin/env python3
"""
golive.py — announce thebardchat's Twitch go-live to Discord. Edge-triggered.

Cron (every few min): polls Helix /streams via a cached app token. When the
channel flips offline->live (or a new stream starts), posts an embed to Discord
via the admin bot (ShaneBrainLegacyBot). State file dedupes so it announces ONCE
per stream. Stdlib only.

  python3 golive.py                 # normal poll (cron)
  python3 golive.py --dry-run       # do everything except post; print the embed
  python3 golive.py --test          # force an announce (uses live data, or sample)
"""
import os
import sys
import json
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

HERE = Path("/home/shanebrain/twitch")
ENVF = HERE / ".env"
DISCORD_ENV = Path("/mnt/shanebrain-raid/shanebrain-core/bot/.env")
STATE = HERE / ".golive_state.json"
TOKCACHE = HERE / ".golive_token.json"
ANNOUNCE_CHANNEL = os.environ.get("DISCORD_GOLIVE_CHANNEL", "1103685981263110296")  # #announcements
TWITCH_URL = "https://twitch.tv/thebardchat"


def envget(path, key):
    if not path.exists():
        return None
    for ln in path.read_text(errors="ignore").splitlines():
        ln = ln.strip()
        if ln.startswith(key + "="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _req(method, url, headers, data=None, form=False):
    if form:
        body = urllib.parse.urlencode(data).encode()
    elif isinstance(data, (dict, list)):
        body = json.dumps(data).encode()
    else:
        body = data.encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as x:
            return x.status, json.loads(x.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except Exception:
            return e.code, None


def app_token(cid, secret):
    if TOKCACHE.exists():
        try:
            c = json.loads(TOKCACHE.read_text())
            if c.get("exp", 0) > time.time() + 120:
                return c["token"]
        except Exception:
            pass
    st, res = _req("POST", "https://id.twitch.tv/oauth2/token",
                   {"Content-Type": "application/x-www-form-urlencoded"},
                   {"client_id": cid, "client_secret": secret,
                    "grant_type": "client_credentials"}, form=True)
    if st != 200:
        raise SystemExit(f"twitch app-token failed [{st}]: {res}")
    TOKCACHE.write_text(json.dumps({"token": res["access_token"],
                                    "exp": time.time() + res.get("expires_in", 3600)}))
    try:
        TOKCACHE.chmod(0o600)
    except Exception:
        pass
    return res["access_token"]


def stream_status(cid, token, login):
    st, res = _req("GET", f"https://api.twitch.tv/helix/streams?user_login={login}",
                   {"Client-Id": cid, "Authorization": f"Bearer {token}"})
    if st != 200:
        raise SystemExit(f"helix streams failed [{st}]: {res}")
    data = res.get("data") or []
    return data[0] if data else None


def announce(stream, dtoken, dry=False):
    title = (stream.get("title") or "Live now!")[:240]
    game = stream.get("game_name") or ""
    thumb = (stream.get("thumbnail_url") or "").replace("{width}", "1280").replace("{height}", "720")
    embed = {"title": title, "url": TWITCH_URL, "color": 0x9146FF,
             "author": {"name": "\U0001F534 thebardchat is LIVE on Twitch!"},
             "description": (f"**{game}**\n\n" if game else "") + f"Come hang out \U0001F49B  {TWITCH_URL}"}
    if thumb:
        embed["image"] = {"url": thumb}
    payload = {"content": f"@everyone  thebardchat is now LIVE — {TWITCH_URL}", "embeds": [embed], "allowed_mentions": {"parse": ["everyone"]}}
    if dry:
        print(json.dumps(payload, indent=2)[:1000])
        return None
    st, res = _req("POST", f"https://discord.com/api/v10/channels/{ANNOUNCE_CHANNEL}/messages",
                   {"Authorization": f"Bot {dtoken}", "Content-Type": "application/json",
                    "User-Agent": "golive/1.0"}, payload)
    if st in (200, 201):
        print("announced -> msg", res.get("id"))
        return res.get("id")
    print(f"discord post failed [{st}]: {res}")
    return None


def main():
    dry = "--dry-run" in sys.argv
    test = "--test" in sys.argv
    cid = envget(ENVF, "TWITCH_CLIENT_ID")
    secret = envget(ENVF, "TWITCH_CLIENT_SECRET")
    login = envget(ENVF, "TWITCH_CHANNEL") or "thebardchat"
    if not cid or not secret:
        raise SystemExit("TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET missing in twitch/.env")
    dtoken = envget(DISCORD_ENV, "DISCORD_TOKEN")
    tok = app_token(cid, secret)
    stream = stream_status(cid, tok, login)
    state = json.loads(STATE.read_text()) if STATE.exists() else {"live": False, "stream_id": None}

    if test:
        announce(stream or {"title": "[TEST] thebardchat go-live wiring check",
                            "game_name": "Just Chatting"}, dtoken, dry=dry)
        return

    live = stream is not None
    sid = stream.get("id") if stream else None
    if live and (not state.get("live") or state.get("stream_id") != sid):
        announce(stream, dtoken, dry=dry)
    print(f"live={live} stream_id={sid} (was live={state.get('live')})")
    if not dry:
        STATE.write_text(json.dumps({"live": live, "stream_id": sid}))


if __name__ == "__main__":
    main()
