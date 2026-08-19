

import os
import random
import logging
import asyncio
from aiohttp import web, ClientSession, ClientTimeout
from pyrogram import idle
from main import VJBot, start_bot
from config import Config, temp

logger = logging.getLogger("keep_alive")

# Module-level strong reference so the task can never be garbage-collected.
_keepalive_task = None


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

    Started BEFORE start_bot() so it runs independently of how long
    bot startup / restart_forwards() (which can resume hours-long
    forwarding jobs) takes to complete.
    """
    if not Config.PING_URL:
        return

    url = Config.PING_URL.rstrip("/") + "/"
    timeout = ClientTimeout(total=15)

    async with ClientSession(timeout=timeout) as session:
        while True:
            jitter = random.uniform(-20, 20)
            sleep_for = max(30, Config.PING_INTERVAL + jitter)
            await asyncio.sleep(sleep_for)

            if temp.forwardings <= 0:
                continue

            try:
                async with session.get(url) as resp:
                    pass
            except Exception as e:
                logger.warning(f"keep_alive: ping failed - {e}")


def _keepalive_done_callback(task):
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        logger.error(f"keep_alive task crashed: {exc}")


def start_keepalive_task():
    """Creates the keep_alive task exactly once, with a strong module-level
    reference (so it can't be garbage-collected) and a done-callback so any
    crash is always logged, never silent."""
    global _keepalive_task
    if _keepalive_task is not None and not _keepalive_task.done():
        return _keepalive_task
    _keepalive_task = asyncio.create_task(keep_alive())
    _keepalive_task.add_done_callback(_keepalive_done_callback)
    return _keepalive_task


async def main():
    await run_web_server()
    # Start keep_alive BEFORE start_bot(): restart_forwards() inside
    # start_bot() can resume hours-long forwarding jobs and won't return
    # until they finish. Creating the task here means it runs concurrently
    # on the event loop from process start, independent of that duration.
    start_keepalive_task()
    await start_bot()
    await idle()

    # Graceful shutdown: stop keep_alive cleanly when idle() returns
    # (bot stopped / process shutting down).
    if _keepalive_task is not None and not _keepalive_task.done():
        _keepalive_task.cancel()
        try:
            await _keepalive_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())

