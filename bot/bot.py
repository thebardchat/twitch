"""
thebardchat Twitch Chat Bot
Powered by twitchio + ShaneBrain local AI (Ollama cluster via MCP)
Deploy as systemd service 'twitch-bot' on Pi 5
"""
import os
import asyncio
import aiohttp
from datetime import datetime, date
from twitchio.ext import commands

TWITCH_TOKEN    = os.environ["TWITCH_OAUTH_TOKEN"]
TWITCH_CHANNEL  = os.environ.get("TWITCH_CHANNEL", "thebardchat")
MCP_URL         = os.environ.get("SHANEBRAIN_MCP_URL", "http://localhost:8100/mcp")
OLLAMA_URL      = os.environ.get("SHANEBRAIN_OLLAMA_URL", "http://localhost:11435")
SOBRIETY_START  = date(2023, 11, 27)
COMMAND_COOLDOWN = 30  # global seconds between !shanebrain calls
USER_COOLDOWN    = 10  # per-user seconds

_sb_last_call = 0
_user_cooldowns: dict[str, float] = {}


class BardBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=TWITCH_TOKEN,
            prefix="!",
            initial_channels=[TWITCH_CHANNEL],
        )

    async def event_ready(self):
        print(f"[BardBot] Connected as {self.nick} to #{TWITCH_CHANNEL}")

    async def event_message(self, message):
        if message.echo:
            return
        await self.handle_commands(message)

    # ── AI Command ──────────────────────────────────────────────
    @commands.command(name="shanebrain", aliases=["sb"])
    async def shanebrain(self, ctx: commands.Context):
        global _sb_last_call
        now = asyncio.get_event_loop().time()

        if now - _sb_last_call < COMMAND_COOLDOWN:
            wait = int(COMMAND_COOLDOWN - (now - _sb_last_call))
            await ctx.send(f"@{ctx.author.name} Hold tight — !shanebrain cools down every {COMMAND_COOLDOWN}s. Try again in {wait}s.")
            return

        user_last = _user_cooldowns.get(ctx.author.name, 0)
        if now - user_last < USER_COOLDOWN:
            return  # silent per-user throttle

        query = ctx.message.content.replace("!shanebrain", "").replace("!sb", "").strip()
        if not query:
            await ctx.send(f"@{ctx.author.name} Ask me something! Usage: !shanebrain <your question>")
            return

        _sb_last_call = now
        _user_cooldowns[ctx.author.name] = now

        try:
            answer = await _ask_ollama(query)
            # Twitch chat max 500 chars
            if len(answer) > 430:
                answer = answer[:427] + "..."
            await ctx.send(f"@{ctx.author.name} 🤖 {answer}")
        except Exception as e:
            print(f"[shanebrain error] {e}")
            await ctx.send(f"@{ctx.author.name} ShaneBrain is thinking too hard — try again in a moment.")

    # ── Sobriety Counter ────────────────────────────────────────
    @commands.command(name="sobriety")
    async def sobriety(self, ctx: commands.Context):
        days = (date.today() - SOBRIETY_START).days
        await ctx.send(f"Shane has been sober for {days} days (since 11/27/2023). One day at a time. ✨")

    # ── Love Quote ──────────────────────────────────────────────
    @commands.command(name="love")
    async def love(self, ctx: commands.Context):
        quotes = [
            "The internet has enough darkness. Be the light someone needed today.",
            "Faith isn't the absence of doubt. It's showing up anyway.",
            "You don't have to perform wellness. You just have to want it.",
            "Real community remembers your name. That's what we're building here.",
            "Local AI, local love — nothing leaves the house without permission.",
            "Sobriety isn't giving something up. It's choosing yourself.",
            "Every stream is a chance to make someone feel less alone.",
        ]
        import random
        await ctx.send(f"💛 {random.choice(quotes)} — thebardchat")

    # ── Crew Info ───────────────────────────────────────────────
    @commands.command(name="crew")
    async def crew(self, ctx: commands.Context):
        await ctx.send(
            "🤖 The MEGA Crew: 17 AI bots running 24/7 on a Pi 5 — Arc (gatekeeper), Sparky (judge), "
            "Blaze (context), Gemini Strategist (growth coach), Weld (code deployer) + 12 more. "
            "All local. All private. github.com/thebardchat/twitch"
        )

    # ── Book Info ───────────────────────────────────────────────
    @commands.command(name="book")
    async def book(self, ctx: commands.Context):
        await ctx.send(
            "📖 'You Probably Think This Book Is About You' — Shane's noir vignette collection. "
            "On Amazon now: amazon.com/dp/B0GT25R5FD | Vol 2 in progress 🖤"
        )

    # ── Discord ─────────────────────────────────────────────────
    @commands.command(name="discord")
    async def discord(self, ctx: commands.Context):
        await ctx.send("🎮 Join the community on Discord! Link in the channel panels below the stream. Love & Light crew only — toxicity gets the boot.")

    # ── Clip ────────────────────────────────────────────────────
    @commands.command(name="clip")
    async def clip(self, ctx: commands.Context):
        await ctx.send(f"@{ctx.author.name} Clip feature coming in Phase 2 — needs Twitch OAuth broadcaster scope. Stay tuned!")

    # ── Schedule ────────────────────────────────────────────────
    @commands.command(name="schedule")
    async def schedule(self, ctx: commands.Context):
        await ctx.send(
            "📅 Stream schedule: ShaneBrain Live (weekly), Family Takeover (monthly), "
            "Noir Night (bi-weekly), Local AI School (monthly). "
            "Follow on Twitch for live notifications! thebardchat.github.io/twitch/"
        )


async def _ask_ollama(prompt: str) -> str:
    """Send prompt to local Ollama cluster and return response."""
    payload = {
        "model": "llama3.1:8b",
        "prompt": (
            "You are ShaneBrain, a helpful AI assistant built for a Twitch chat. "
            "Keep answers under 350 characters. Be warm, helpful, and honest. "
            f"Question: {prompt}"
        ),
        "stream": False,
        "options": {"num_predict": 120},
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=20),
        ) as resp:
            data = await resp.json()
            return data.get("response", "I don't have an answer for that right now.").strip()


if __name__ == "__main__":
    bot = BardBot()
    bot.run()
