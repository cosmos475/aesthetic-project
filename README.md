# 🤖 VJ Forward Bot (Simple Bot)

A multi-tenant **Telegram auto-forward bot** built on **Pyrogram (MTProto)**. Each Telegram user can connect their own bot or userbot session, configure a source and destination (channel, normal group, or forum/topic-wise supergroup), and forward messages — either the newest ones or a specific ID/link range — with filters, custom captions, buttons, and duplicate detection.

> Because it uses MTProto (via a userbot session) instead of only the official Bot API, it can read full chat history and forward from private sources that a plain bot account couldn't otherwise access.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Commands](#-commands)
- [Menus & Buttons](#-menus--buttons)
- [Project Structure](#-project-structure)
- [Technologies Used](#-technologies-used)
- [Environment Variables](#-environment-variables)
- [Local Setup](#-local-setup)
- [Deployment (Render)](#-deployment-render)
- [Configuration Details](#-configuration-details)
- [Implementation Notes](#-implementation-notes)
- [Prerequisites & Permissions](#-prerequisites--permissions)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🔎 Overview

This bot lets any Telegram user:

1. Connect their **own bot token** or **own userbot session** (via `/settings`).
2. Set a **Source** (channel, normal group, or a topic inside a forum-enabled supergroup).
3. Set a **Destination** (channel, normal group, or a specific topic).
4. Forward the **latest** messages, or a **specific range**, from source to destination — with optional captions, inline buttons, content filters, and duplicate-skipping.

It is designed as a **self-service** forwarding tool: every user manages their own bot/userbot, source, destination, and settings independently, all stored per `user_id` in MongoDB.

---

## ✨ Features

### Core Forwarding
- 🔗 **Bot or Userbot mode** — attach your own Bot API token, or log in with a full userbot session (phone number + OTP/2FA) for MTProto-level access.
- 📥 **Source Setup** — Channel, Normal Group, or Supergroup Topic.
- 📤 **Destination Setup** — Channel, Normal Group, or Supergroup Topic.
- ⚡ **Latest Forward** — forward everything up to the newest message in the source.
- 🎯 **Range Forward** — forward a specific range, given as forwarded messages or `t.me` links (supports both normal 2‑segment links and 3‑segment forum-topic links).
- ⏸️ **Cancel/Stop** running forwards at any time (`/stop`).
- 🔁 **Resumable** — in-progress forwards are restored automatically after a bot restart (`restart_forwards`).

### Customization (`/settings`)
- 🖋️ **Custom Caption** with placeholders (`{filename}`, `{size}`, `{caption}`).
- ⏹ **Custom Inline Button** on forwarded messages (`[Text][buttonurl:https://link]` syntax).
- 🕵️ **Content Filters** — toggle forwarding of text, document, video, photo, audio, voice, animation, sticker, poll.
- 💾 **Min/Max file size** limits.
- 🕹 **Extension blacklist** and **🚥 Keyword whitelist**.
- 🔁 **Skip duplicates** (requires a personal MongoDB URL for tracking).
- 🏷 **Forward-tag mode** and **🔒 Protect content** toggle.
- 🗃 **Personal MongoDB URL** for duplicate tracking.
- 🏢 **Branding** (owner-only) — optional "Developer" button on the bot's main menu.

### Utilities
- 🧹 `/unequify` — scans a chat (userbot required) and removes duplicate files.
- 📊 `/status` and system stats (RAM/CPU/disk) via the Help menu.
- 📢 `/broadcast` (owner-only, reply-based) to message all bot users.
- 🔄 `/restart` and `/resetall` (owner-only) for maintenance.

---

## 💬 Commands

| Command | Scope | Description |
|---|---|---|
| `/start` | Private | Shows the welcome message and main menu. |
| `/settings` | Anywhere | Opens the Settings panel (Bots, Caption, Button, Filters, MongoDB, Extra Settings, Branding). |
| `/sourcesetup` | Private | Opens the Source Setup menu. |
| `/destinationsetup` | Private | Opens the Destination Setup menu. |
| `/setsource` | Group/Topic | Sent **inside** a group or forum topic to capture it as the source (requires capture mode armed from `/sourcesetup`). |
| `/setdestination` | Group/Topic | Sent **inside** a group or forum topic to capture it as the destination. |
| `/forward` | Private | Starts a forward job — choose **Latest** or **Range** mode. |
| `/stop` | Private | Cancels the currently running forward job. |
| `/reset` | Private | Resets the user's own settings. |
| `/unequify` | Private | Removes duplicate files from a chat (userbot required). |
| `/broadcast` (reply) | Private, owner only | Broadcasts the replied message to every bot user. |
| `/restart` | Private, owner only | Pulls latest code and restarts the process. |
| `/resetall` | Private, owner only | Resets settings for all users. |

---

## 🎛 Menus & Buttons

**Main Menu** (`/start`): `📥 Source Setup` · `📤 Destination Setup` · `👨‍💻 Help` · `💁 About` · `⚙ Settings` (+ optional `👨‍💻 Developer` button if branding is enabled).

**Source / Destination Setup** → choose type:
- 📡 **Channel** — set by forwarding a message from the channel, or pasting its `t.me` link.
- 👥 **Normal Group** — arms a 10-minute capture window; send `/setsource` or `/setdestination` inside the group to confirm.
- 🗂 **Supergroup Topics** — same capture flow, but run **inside the specific topic** (not the "General" topic) so the bot can capture the correct `thread_id`.

**Settings Panel** (`/settings`):
- 🤖 **Bots** — Add/Remove your Bot token or Userbot session.
- 🖋️ **Caption** — Add/View/Delete a custom caption template.
- ⏹ **Button** — Add/View/Remove a custom inline button on forwarded posts.
- 🕵️ **Filters** — toggle which content types get forwarded.
- 🗃 **MongoDB** — Add/View/Remove your personal DB URL (used for duplicate tracking).
- 🧪 **Extra Settings** — Min/Max size limits, Keywords, Extensions.
- 🏢 **Branding** *(owner only)* — toggle and set the Developer button link.

**Forward flow** (`/forward`): `⚡ Latest Forward` or `🎯 Range Forward` → confirmation screen (`Yes`/`No`) → live progress message with a `Cancel` button → completion summary.

---

## 🗂 Project Structure

```
aesthetic-project-main/
├── app.py                  # Entry point: starts an aiohttp health server + the bot on one event loop
├── main.py                 # Pyrogram Client setup, custom iter_messages() helper, start_bot()
├── config.py                # Loads environment variables into Config / temp (in-memory state)
├── database.py               # MongoDB access layer (Db class) - users, sources, destinations, configs, capture mode, branding
├── script.py                # All user-facing text templates (Script class)
├── requirements.txt          # Python dependencies
├── Procfile                 # Process command for platforms like Render/Heroku
├── run cmd.txt               # Manual run command reference
├── .python-version           # Pins the Python runtime version
├── LICENCE                  # Mozilla Public License 2.0
└── plugins/
    ├── commands.py           # /start, /restart, Help/About/Status callbacks
    ├── settings.py           # /settings panel and all its submenus
    ├── source.py             # Source Setup (channel/group/topic) + /setsource group handler
    ├── destination.py         # Destination Setup (channel/group/topic) + /setdestination group handler
    ├── public.py              # /forward entry point, Latest/Range mode selection, link/ID parsing
    ├── regix.py               # Core forwarding engine: iterate, filter, copy/forward, progress updates, /stop
    ├── test.py                # Bot/userbot session onboarding (CLIENT class), config get/update helpers
    ├── unequeify.py            # /unequify duplicate-file cleanup
    ├── broadcast.py            # /broadcast (owner only)
    ├── db.py                  # Per-user MongoDB connector for duplicate tracking
    └── utils.py                # STS - in-memory forward job state/progress tracker
```

---

## 🛠 Technologies Used

| Category | Technology |
|---|---|
| Language | Python **3.10.13** (pinned via `.python-version`) |
| Telegram Client | [Pyrogram](https://pypi.org/project/pyrofork/) via **pyrofork** fork (MTProto) |
| Crypto acceleration | `TgCrypto` / `tgcrypto` |
| Ask/listen patch | `pyropatch` (adds `Client.ask()` for conversational prompts) |
| Database | MongoDB via `motor` (async driver), `pymongo[srv]`, `umongo`, `Dnspython` |
| Web server | `aiohttp` (health-check endpoint for host platforms) |
| System stats | `psutil` |
| Misc | `humanize`, `pytz` |

### `requirements.txt`
```
pyrofork
tgcrypto
pyropatch
humanize
motor==2.5.1
TgCrypto
Dnspython
pymongo[srv]==3.12.3
umongo==3.0.1
psutil
pytz
aiohttp
```

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `API_ID` | ✅ Yes | — | Telegram API ID from [my.telegram.org](https://my.telegram.org). |
| `API_HASH` | ✅ Yes | — | Telegram API Hash from [my.telegram.org](https://my.telegram.org). |
| `BOT_TOKEN` | ✅ Yes | — | Bot token from [@BotFather](https://t.me/BotFather) for the main service bot. |
| `BOT_OWNER` | ✅ Yes | — | Your numeric Telegram user ID — grants access to owner-only commands (`/restart`, `/resetall`, `/broadcast`, Branding). |
| `DATABASE_URI` | ✅ Yes | — | MongoDB connection string for the bot's main database. |
| `DATABASE_NAME` | ❌ No | `vj-forward-bot` | Name of the MongoDB database to use. |
| `BOT_SESSION` | ❌ No | `vjbot` | Pyrogram session name. |
| `PORT` | ❌ No | `5000` | Port for the built-in aiohttp health server (usually set automatically by the host). |

> Per-user bot tokens, userbot sessions, and MongoDB URLs (for duplicate tracking) are **not** environment variables — they're added by each user at runtime through `/settings`, and stored in the main database.

---

## 💻 Local Setup

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd aesthetic-project-main
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file or export variables directly:
```bash
export API_ID="12345678"
export API_HASH="your_api_hash"
export BOT_TOKEN="your_bot_token"
export BOT_OWNER="your_telegram_user_id"
export DATABASE_URI="mongodb+srv://user:pass@cluster.mongodb.net"
export DATABASE_NAME="vj-forward-bot"
```

**5. Run the bot**
```bash
python3 app.py
```
`app.py` starts both the aiohttp health server and the Pyrogram client on the same asyncio event loop.

---

## 🚀 Deployment (Render)

This project is pre-configured for **Render** (a `Procfile` and `.python-version` are included).

| Setting | Value |
|---|---|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python3 app.py` (matches the `Procfile`: `web: python3 app.py`) |
| **Environment** | Python 3 (version pinned by `.python-version` → `3.10.13`) |
| **Instance Type** | Web Service (the built-in aiohttp server satisfies Render's port-binding health check) |

**Required Environment Variables on Render:**
`API_ID`, `API_HASH`, `BOT_TOKEN`, `BOT_OWNER`, `DATABASE_URI` (plus optional `DATABASE_NAME`, `BOT_SESSION`).

**Deployment notes:**
- Render's free web-service tier requires the app to bind to `$PORT` — this is already handled by `run_web_server()` in `app.py`.
- On a free tier, the service can idle/sleep; the bot does not include a built-in keep-alive pinger in this codebase, so an external uptime pinger may be needed to prevent idle sleep during long forward jobs.
- `/restart` (owner-only) runs `git pull -f && pip3 install -r requirements.txt` and re-execs the process — this only works if the deployment environment has git available and write access to the repo checkout.

**Other platforms:** any host that can run a long-lived Python process and expose a port (Heroku, Railway, a VPS, Docker) will work — just set the same environment variables and use `python3 app.py` (or `gunicorn app:app` alongside `python3 main.py`, as referenced in `run cmd.txt`) as the start command.

---

## ⚙️ Configuration Details

- **Per-user data model** — everything (source, destination, bot/userbot, filters, caption, button, capture-mode state) is stored in MongoDB keyed by the Telegram `user_id`, so many people can use the same bot deployment independently.
- **Capture Mode** — setting a Normal Group or Supergroup Topic as source/destination works via a **10-minute armed window**: after choosing the type in `/sourcesetup` or `/destinationsetup`, you must send `/setsource` or `/setdestination` **inside** the target group/topic while the window is active.
- **Filters default** — all content types (`text`, `document`, `video`, `photo`, `audio`, `voice`, `animation`, `sticker`, `poll`) are **enabled** by default; duplicate-skip is **on** by default; forward-tag and protect-content are **off** by default.
- **Duplicate tracking** requires the user to supply their own MongoDB URL under Settings → MongoDB — this is a separate database from the main `DATABASE_URI` used to run the bot itself.

---

## 🧩 Implementation Notes

- **MTProto, not just Bot API** — the bot runs on `pyrofork` (a Pyrogram fork), which means users can attach a full **userbot session** for capabilities the plain Bot API doesn't allow (e.g., reading full chat history for `/unequify`, or accessing private-chat history for range forwarding).
- **Forum/Topic handling** — Telegram assigns forum-enabled supergroups a distinct chat type at the MTProto layer. Group/topic handlers explicitly match this type (in addition to normal group/supergroup) so that topic-based sources and destinations work correctly.
- **Message link parsing** — supports both standard 2-segment links (`t.me/c/<chat_id>/<message_id>`) and 3-segment forum-topic links (`t.me/c/<chat_id>/<thread_id>/<message_id>`) for Range Forward.
- **Single event loop** — `app.py` runs the aiohttp health server and the Pyrogram client on the same asyncio loop, which is what allows Motor (async MongoDB) and Pyrogram to share context safely without threads.
- **Resumability** — `restart_forwards()` (in `plugins/regix.py`) is called on startup to resume any forward jobs that were interrupted by a restart.
- **Database** — uses `motor` (async MongoDB driver) for the main bot database, plus a lazily-created per-user connection (`plugins/db.py`) for personal duplicate-tracking databases.

---

## ✅ Prerequisites & Permissions

- A Telegram **Bot Token** from [@BotFather](https://t.me/BotFather).
- A Telegram **API ID / API Hash** from [my.telegram.org](https://my.telegram.org).
- A **MongoDB** database (e.g. a free MongoDB Atlas cluster) reachable via a `mongodb+srv://` URI.
- For each user's forwarding setup:
  - The bot/userbot must be an **admin** in the destination chat (to post messages).
  - For private source chats, the bot/userbot must be a **member or admin** of the source.
  - When capturing a **Normal Group or Topic**, **Anonymous Admin mode should be OFF** for the bot's own admin rights so it can reliably identify the chat/topic when `/setsource` or `/setdestination` is sent.

---

## 🧯 Troubleshooting

| Issue | Likely Cause / Fix |
|---|---|
| Bot doesn't respond to `/setsource` or `/setdestination` in a group | Capture mode wasn't armed (re-run Source/Destination Setup and choose the type again), or you're not sending the command inside the correct topic. |
| Nothing happens in a Topics-enabled supergroup | Make sure you're running the command **inside a specific topic**, not the "General" area, and that the bot is an admin with Anonymous Admin mode off. |
| "Invalid message reference" during Range Forward | The link format wasn't recognized, or (for a topic source) the link's topic doesn't match the configured source topic. |
| `BOT_METHOD_INVALID` type errors | Some MTProto methods (e.g. reading full chat history) are only available to a **userbot** session, not a plain Bot API token — add a userbot under Settings → Bots. |
| Duplicate-skip doesn't work | Add a personal MongoDB URL under Settings → MongoDB — duplicate tracking needs its own database per user. |
| Bot goes idle on Render free tier | Free web services can sleep after inactivity; consider an external uptime pinger hitting the health endpoint (`/`). |

---

## 📄 License

Licensed under the **Mozilla Public License 2.0** — see the [`LICENCE`](./LICENCE) file for full terms.

---

## 🙌 Credits

Built on top of the [Pyrogram](https://github.com/pyrogram/pyrogram) / [pyrofork](https://github.com/Mayuri-Chan/pyrofork) MTProto framework, with `pyropatch` for conversational (`ask()`) flows and `motor`/MongoDB for persistence.
