

from os import environ 

class Config:
    API_ID = int(environ.get("API_ID", ""))
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_SESSION = environ.get("BOT_SESSION", "vjbot") 
    DATABASE_URI = environ.get("DATABASE_URI", "")
    DATABASE_NAME = environ.get("DATABASE_NAME", "vj-forward-bot")
    BOT_OWNER = int(environ.get("BOT_OWNER", ""))

    # Keep-alive self-ping settings (prevents Render free-tier sleep during active forwarding).
    # RENDER_EXTERNAL_URL is auto-injected by Render for every web service — no manual setup needed.
    # PING_URL lets you override it manually (e.g. for local testing or non-Render hosts).
    PING_URL = environ.get("PING_URL") or environ.get("RENDER_EXTERNAL_URL", "")
    PING_INTERVAL = int(environ.get("PING_INTERVAL", 540))  # seconds, default 9 min


class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []

