#!/usr/bin/env python3
"""
golive.py — announce thebardchat's Twitch go-live to Discord. Edge-triggered.

Cron (every few min): polls Helix /streams via a cached app token.
  * offline->live: posts a LIVE embed to #announcements, pinging @Stream Squad
    (falls back to @everyone if the squad role isn't set up).
  * live->offline: posts a "stream ended" wrap-up embed with the VOD replay link,
    and drops that replay into the Stream Squad channel as a member perk.
State file dedupes so each transition fires once. Stdlib only.

  python3 golive.py                 # normal poll (cron)
  python3 golive.py --dry-run       # do everything except post; print the payloads
  python3 golive.py --test          # force a LIVE announce (live data, or sample)
  python3 golive.py --test --offline# force a wrap-up/VOD-drop (uses latest VOD)
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
GUILD_ID = os.environ.get("DISCORD_GUILD", "1103685980633972819")
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


def latest_vod(cid, token, user_id):
    """Most recent archived VOD for the channel, or None (VODs can lag a minute)."""
    if not user_id:
        return None
    st, res = _req("GET",
                   f"https://api.twitch.tv/helix/videos?user_id={user_id}&type=archive&first=1",
                   {"Client-Id": cid, "Authorization": f"Bearer {token}"})
    if st != 200:
        return None
    data = res.get("data") or []
    return data[0] if data else None


def _squad_role_id():
    """Stream Squad role id from stream_squad.json, or None."""
    return _squad_get("role_id")


def _squad_channel_id():
    """Stream Squad private channel id from stream_squad.json, or None."""
    return _squad_get("squad_channel_id")


def _squad_get(key):
    try:
        s = json.loads((HERE / "stream_squad.json").read_text())
        return s.get(key)
    except Exception:
        return None


def _discord_post(channel, payload, dtoken, label):
    st, res = _req("POST", f"https://discord.com/api/v10/channels/{channel}/messages",
                   {"Authorization": f"Bot {dtoken}", "Content-Type": "application/json",
                    "User-Agent": "golive/1.0"}, payload)
    if st in (200, 201):
        print(f"{label} -> msg", res.get("id"))
        return res.get("id")
    print(f"{label} failed [{st}]: {res}")
    return None


def announce(stream, dtoken, dry=False):
    title = (stream.get("title") or "Live now!")[:240]
    game = stream.get("game_name") or ""
    thumb = (stream.get("thumbnail_url") or "").replace("{width}", "1280").replace("{height}", "720")
    embed = {"title": title, "url": TWITCH_URL, "color": 0x9146FF,
             "author": {"name": "\U0001F534 thebardchat is LIVE on Twitch!"},
             "description": (f"**{game}**\n\n" if game else "") + f"Come hang out \U0001F49B  {TWITCH_URL}"}
    if thumb:
        embed["image"] = {"url": thumb}
    role_id = _squad_role_id()
    if role_id:
        content = f"<@&{role_id}>  thebardchat is now LIVE — {TWITCH_URL}"
        allowed = {"roles": [role_id]}
    else:
        content = f"@everyone  thebardchat is now LIVE — {TWITCH_URL}"
        allowed = {"parse": ["everyone"]}
    payload = {"content": content, "embeds": [embed], "allowed_mentions": allowed}
    if dry:
        print("[announce]", json.dumps(payload, indent=2)[:800])
        return None
    return _discord_post(ANNOUNCE_CHANNEL, payload, dtoken, "announced")


def wrap_up(last, vod, dtoken, dry=False):
    """Post a 'stream ended' embed + drop the replay into the squad channel."""
    title = (last.get("title") or "Stream")[:240]
    vod_url = (vod or {}).get("url")
    dur = (vod or {}).get("duration", "")
    desc = "Thanks for hanging out \U0001F49B"
    if vod_url:
        desc += f"\n\n\U0001F4FA **Watch the replay:** {vod_url}"
    else:
        desc += "\n\nVOD is still processing — it'll be up on Twitch shortly."
    embed = {"title": f"◼️ Stream ended — {title}"[:250],
             "url": vod_url or TWITCH_URL, "color": 0x5C16C5,
             "author": {"name": "thebardchat went offline"},
             "description": desc}
    if dur:
        embed["footer"] = {"text": f"Streamed for {dur}"}
    payload = {"embeds": [embed], "allowed_mentions": {"parse": []}}
    if dry:
        print("[wrap-up]", json.dumps(payload, indent=2)[:800])
    else:
        _discord_post(ANNOUNCE_CHANNEL, payload, dtoken, "wrap-up")

    # squad perk: replay link dropped into the squad-only channel, pinging the role
    role_id = _squad_role_id()
    squad_chan = _squad_channel_id()
    if squad_chan and vod_url:
        ping = f"<@&{role_id}> " if role_id else ""
        sp = {"content": f"{ping}\U0001F4FA Replay is up — **{title}**\n{vod_url}",
              "allowed_mentions": {"roles": [role_id] if role_id else []}}
        if dry:
            print("[squad-drop]", json.dumps(sp)[:400])
        else:
            _discord_post(squad_chan, sp, dtoken, "squad VOD drop")


def create_event(stream, dtoken, dry=False):
    """Create a Discord Scheduled Event pointing at the Twitch stream."""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    start = (now + datetime.timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    end = (now + datetime.timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    body = {"name": (stream.get("title") or "thebardchat LIVE")[:100],
            "privacy_level": 2, "scheduled_start_time": start, "scheduled_end_time": end,
            "entity_type": 3, "entity_metadata": {"location": TWITCH_URL},
            "description": f"Live on Twitch — {TWITCH_URL}"[:1000]}
    if dry:
        print("[event create]", json.dumps(body)[:400])
        return None
    st, res = _req("POST", f"https://discord.com/api/v10/guilds/{GUILD_ID}/scheduled-events",
                   {"Authorization": f"Bot {dtoken}", "Content-Type": "application/json",
                    "User-Agent": "golive/1.0"}, body)
    if st in (200, 201):
        print("event created ->", res.get("id"))
        return res.get("id")
    print(f"event create failed [{st}]: {res}")
    return None


def end_event(event_id, dtoken, dry=False):
    if not event_id:
        return
    if dry:
        print("[event end] would delete", event_id)
        return
    st, _ = _req("DELETE", f"https://discord.com/api/v10/guilds/{GUILD_ID}/scheduled-events/{event_id}",
                 {"Authorization": f"Bot {dtoken}", "User-Agent": "golive/1.0"})
    print(f"event ended [{st}]")


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
        if "--offline" in sys.argv:
            uid = state.get("user_id") or (stream or {}).get("user_id")
            vod = latest_vod(cid, tok, uid)
            wrap_up(state if state.get("title") else {"title": "[TEST] wrap-up wiring check"},
                    vod, dtoken, dry=dry)
        else:
            announce(stream or {"title": "[TEST] thebardchat go-live wiring check",
                                "game_name": "Just Chatting"}, dtoken, dry=dry)
        return

    live = stream is not None
    sid = stream.get("id") if stream else None
    event_id = state.get("event_id")

    if live and (not state.get("live") or state.get("stream_id") != sid):
        announce(stream, dtoken, dry=dry)
        new_eid = create_event(stream, dtoken, dry=dry)
        if new_eid:
            event_id = new_eid
    if state.get("live") and not live:
        vod = latest_vod(cid, tok, state.get("user_id"))
        wrap_up(state, vod, dtoken, dry=dry)
        end_event(state.get("event_id"), dtoken, dry=dry)
        event_id = None

    print(f"live={live} stream_id={sid} (was live={state.get('live')}) event={event_id}")
    if not dry:
        if live:
            STATE.write_text(json.dumps({
                "live": True, "stream_id": sid,
                "user_id": stream.get("user_id"),
                "title": stream.get("title"),
                "game": stream.get("game_name"),
                "started_at": stream.get("started_at"),
                "event_id": event_id,
            }))
        else:
            STATE.write_text(json.dumps({"live": False, "stream_id": None}))


if __name__ == "__main__":
    main()
