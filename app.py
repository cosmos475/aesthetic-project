

import os
import asyncio
from aiohttp import web
from pyrogram import idle
from main import VJBot, start_bot


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


async def main():
    await run_web_server()
    await start_bot()
    await idle()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())

