import os
import random
import logging
import traceback
import asyncio
from aiohttp import web, ClientSession, ClientTimeout
from pyrogram import idle
from main import VJBot, start_bot
from config import Config, temp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("keep_alive")


async def health(request):
    return web.Response(text="Bot is Running")


async def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    server_app = web.Application()
    server_app.router.add_get("/", health)
    runner = web.AppRunner(server_app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()


async def keep_alive():
    logger.info(f"[KEEPALIVE_BOOT] task started, PING_URL={Config.PING_URL!r}, PING_INTERVAL={Config.PING_INTERVAL}")

    if not Config.PING_URL:
        logger.warning("[KEEPALIVE_NO_URL] no PING_URL/RENDER_EXTERNAL_URL — task exiting now")
        return

    url = Config.PING_URL.rstrip("/") + "/"
    timeout = ClientTimeout(total=15)
    cycle = 0

    try:
        async with ClientSession(timeout=timeout) as session:
            logger.info("[KEEPALIVE_SESSION_OK] ClientSession created")
            while True:
                cycle += 1
                jitter = random.uniform(-20, 20)
                sleep_for = max(30, Config.PING_INTERVAL + jitter)
                logger.info(f"[KEEPALIVE_CYCLE {cycle}] sleeping {sleep_for:.1f}s")
                await asyncio.sleep(sleep_for)

                fwd = temp.forwardings
                logger.info(f"[KEEPALIVE_CHECK {cycle}] temp.forwardings={fwd}")

                if fwd <= 0:
                    logger.info(f"[KEEPALIVE_SKIP {cycle}] forwardings<=0, skipping ping")
                    continue

                try:
                    async with session.get(url) as resp:
                        logger.info(f"[KEEPALIVE_PING_OK {cycle}] {url} -> HTTP {resp.status}")
                except Exception as e:
                    logger.warning(f"[KEEPALIVE_PING_FAIL {cycle}] {type(e).__name__}: {e}")
    except Exception as e:
        logger.error(f"[KEEPALIVE_FATAL] task dying: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise


def _keepalive_done_callback(task):
    if task.cancelled():
        logger.warning("[KEEPALIVE_DONE] task was cancelled")
        return
    exc = task.exception()
    if exc:
        logger.error(f"[KEEPALIVE_DONE] task ended with exception: {exc}")
        logger.error("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    else:
        logger.warning("[KEEPALIVE_DONE] task ended normally (should never happen — infinite loop exited)")


async def main():
    await run_web_server()
    await start_bot()
    keepalive_task = asyncio.create_task(keep_alive())   # strong ref held
    keepalive_task.add_done_callback(_keepalive_done_callback)
    global _KEEPALIVE_TASK_REF
    _KEEPALIVE_TASK_REF = keepalive_task                 # module-level ref, GC-proof
    await idle()


_KEEPALIVE_TASK_REF = None

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
