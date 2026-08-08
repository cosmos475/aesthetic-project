

import os
import random
import logging
import asyncio
from aiohttp import web, ClientSession, ClientTimeout
from pyrogram import idle
from main import VJBot, start_bot
from config import Config, temp

logger = logging.getLogger("keep_alive")


async def health(request):
    return web.Response(text="Bot is Running")


async def run_web_server():
    """Minimal aiohttp server bound to $PORT, running on the same event
    loop as the Pyrogram client. No threads, no separate loop -- this is
    what lets Motor and Pyrogram share one asyncio context."""
    port = int(os.environ.get("PORT", 5000))
    server_app = web.Application()
    server_app.router.add_get("/", health)
    runner = web.AppRunner(server_app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()


async def keep_alive():
    """Self-pings the service's own health endpoint every ~9 minutes,
    but ONLY while temp.forwardings > 0 (i.e. an active forward job is
    running). This keeps Render's free-tier instance awake for the
    duration of a forward without pinging 24/7 when the bot is idle.

    Does not touch forwarding logic at all -- it only reads the existing
    temp.forwardings counter that plugins/regix.py already maintains.
    """
    if not Config.PING_URL:
        logger.warning(
            "keep_alive: no PING_URL / RENDER_EXTERNAL_URL found in env — "
            "self-ping disabled. Set PING_URL manually if not on Render."
        )
        return

    url = Config.PING_URL.rstrip("/") + "/"
    timeout = ClientTimeout(total=15)

    async with ClientSession(timeout=timeout) as session:
        while True:
            # small random jitter so the interval isn't perfectly robotic
            jitter = random.uniform(-20, 20)
            await asyncio.sleep(max(30, Config.PING_INTERVAL + jitter))

            if temp.forwardings <= 0:
                continue  # nothing forwarding right now, skip this cycle

            try:
                async with session.get(url) as resp:
                    logger.info(f"keep_alive: pinged {url} -> {resp.status}")
            except Exception as e:
                logger.warning(f"keep_alive: ping failed - {e}")


async def main():
    await run_web_server()
    await start_bot()
    asyncio.create_task(keep_alive())
    await idle()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())

