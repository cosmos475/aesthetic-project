
import re
import asyncio 
from .utils import STS
from database import Db, db
from config import temp 
from script import Script
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait 
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate as PrivateChat
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified, ChannelPrivate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


@Client.on_message(filters.private & filters.command(["forward"]))
async def run(bot, message):
    user_id = message.from_user.id
    _bot = await db.get_bot(user_id)
    if not _bot:
      _bot = await db.get_userbot(user_id)
      if not _bot:
          return await message.reply("<code>You didn't added any bot. Please add a bot using /settings !</code>")

    src = await db.get_source(user_id)
    if not src:
       return await message.reply_text("<b>No source configured. Please set a source using Source Setup first.</b>")
    chat_id = src['chat_id']
    title = src['title']
    src_type = src.get('type', 'channel')
    src_thread_id = src.get('thread_id')

    dst = await db.get_destination(user_id)
    if not dst:
       return await message.reply_text("please set a destination in Destination Setup before forwarding")
    toid = dst['chat_id']
    to_title = dst['title']
    thread_id = dst.get('thread_id')

    temp.FWD_SETUP = getattr(temp, 'FWD_SETUP', {})
    temp.FWD_SETUP[user_id] = {"chat_id": chat_id, "title": title, "src_type": src_type, "src_thread_id": src_thread_id, "toid": toid, "to_title": to_title, "thread_id": thread_id, "_bot": _bot}
    await start_range_forward(bot, message, user_id)


async def start_range_forward(bot, message, user_id):
    setup = getattr(temp, 'FWD_SETUP', {}).get(user_id)
    if not setup:
        return await bot.send_message(user_id, "session expired, run /forward again")
    chat_id = setup["chat_id"]
    title = setup["title"]
    src_type = setup.get("src_type", "channel")
    src_thread_id = setup.get("src_thread_id")
    toid = setup["toid"]
    to_title = setup["to_title"]
    thread_id = setup.get("thread_id")
    _bot = setup["_bot"]

    if src_type == "channel":
        range_prompt_first = "<b>❪ RANGE FORWARD ❫\n\nSend the FIRST message link/ID of the range (send the message forwarded from source, or its link).\n/cancel - cancel this process</b>"
        range_prompt_last = "<b>❪ RANGE FORWARD ❫\n\nNow send the LAST message link/ID of the range.\n/cancel - cancel this process</b>"
    else:
        range_prompt_first = "<b>❪ RANGE FORWARD ❫\n\nSend the LINK of the FIRST message you want to forward (e.g. https://t.me/c/12345/67).\n/cancel - cancel this process</b>"
        range_prompt_last = "<b>❪ RANGE FORWARD ❫\n\nNow send the LINK of the LAST message you want to forward.\n/cancel - cancel this process</b>"

    first_msg = await bot.ask(user_id, range_prompt_first)
    if first_msg.text and first_msg.text.startswith('/'):
        return await first_msg.reply_text(Script.CANCEL)
    skip = await _extract_msg_id(first_msg, chat_id, src_type, src_thread_id)
    if skip is None:
        return await first_msg.reply_text("<b>Invalid message reference</b>")

    last_msg = await bot.ask(user_id, range_prompt_last)
    if last_msg.text and last_msg.text.startswith('/'):
        return await last_msg.reply_text(Script.CANCEL)
    last_msg_id = await _extract_msg_id(last_msg, chat_id, src_type, src_thread_id)
    if last_msg_id is None:
        return await last_msg.reply_text("<b>Invalid message reference</b>")

    forward_id = f"{user_id}-{last_msg.id}"
    buttons = [[
        InlineKeyboardButton('Yes', callback_data=f"start_public_{forward_id}"),
        InlineKeyboardButton('No', callback_data="close_btn")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)

    src_label = {"channel": "📡 Channel", "group": "👥 Normal Group", "topic": "🗂 Supergroup Topic"}.get(src_type, "📡 Channel")
    expected_total = max(1, int(last_msg_id) - int(skip) + 1)
    per_msg_delay = 1 if _bot['is_bot'] else 10
    eta_seconds = expected_total * per_msg_delay
    eta = _format_duration(eta_seconds)
    await bot.send_message(
        user_id,
        text=Script.RANGE_CONFIRM.format(
            from_chat=title, src_label=src_label, to_chat=to_title,
            first_id=skip, last_id=last_msg_id, expected_total=expected_total,
            delay=per_msg_delay, eta=eta,
            botname=_bot['name'], botuname=_bot['username']
        ),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
    STS(forward_id).store(chat_id, toid, int(skip), int(last_msg_id), thread_id)
    getattr(temp, 'FWD_SETUP', {}).pop(user_id, None)


def _format_duration(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s or not parts:
        parts.append(f"{s}s")
    return " ".join(parts)


# Telegram message link formats:
#   Channel / normal group:  https://t.me/c/<internal_id>/<message_id>            (2 segments)
#   Forum topic:              https://t.me/c/<internal_id>/<thread_id>/<message_id> (3 segments)
# The old regex only matched the 2-segment form, so any topic-group link (which always
# has the extra thread_id segment) silently failed to match and returned None --
# that's why topic-source Range Forward showed "Invalid message reference" with no error/log.
_MSG_LINK_RE = re.compile(
    r"(?:https://)?(?:t\.me/|telegram\.me/|telegram\.dog/)c/(\d+)/(\d+)(?:/(\d+))?"
)


def _parse_msg_link(text):
    """Parses a t.me/c/... link. Returns (message_id, thread_id) or (None, None).

    3-segment link (chat_id/thread_id/message_id) -> topic message, thread_id set.
    2-segment link (chat_id/message_id) -> normal message, thread_id is None.
    """
    if not text:
        return None, None
    match = _MSG_LINK_RE.search(text.strip().replace("?single", ""))
    if not match:
        return None, None
    _chat_part, second, third = match.groups()
    if third is not None:
        return int(third), int(second)
    return int(second), None


async def _extract_msg_id(msg, expected_chat_id, src_type="channel", expected_thread_id=None):
    """Accepts a t.me link (any source type) or a forwarded message (channel sources only).

    Group/topic sources require a link because a forwarded message from a group/topic
    doesn't reliably carry back the original chat/thread info the way a channel forward does.
    For topic sources, the link's thread_id must match the configured source topic --
    otherwise a link pasted from the wrong topic would silently forward from the wrong place.
    """
    if msg.text and not msg.forward_date:
        message_id, thread_id = _parse_msg_link(msg.text)
        if message_id is None:
            return None
        if src_type == "topic" and expected_thread_id is not None and thread_id != expected_thread_id:
            return None
        return message_id
    elif src_type == "channel" and msg.forward_from_chat and msg.forward_from_chat.type in [enums.ChatType.CHANNEL, 'supergroup']:
        return msg.forward_from_message_id
    return None

