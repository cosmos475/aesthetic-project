

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

    dst = await db.get_destination(user_id)
    if not dst:
       return await message.reply_text("please set a destination in Destination Setup before forwarding")
    toid = dst['chat_id']
    to_title = dst['title']
    thread_id = dst.get('thread_id')

    mode_buttons = [[
        InlineKeyboardButton('⚡ Latest Forward', callback_data=f"fwdmode_latest_{user_id}"),
        InlineKeyboardButton('🎯 Range Forward', callback_data=f"fwdmode_range_{user_id}")
    ]]
    temp.FWD_SETUP = getattr(temp, 'FWD_SETUP', {})
    temp.FWD_SETUP[user_id] = {"chat_id": chat_id, "title": title, "toid": toid, "to_title": to_title, "thread_id": thread_id, "_bot": _bot}
    await message.reply_text(
        "<b>❪ CHOOSE FORWARD MODE ❫</b>\n\n<b>⚡ Latest Forward</b> — forward up to the latest message from source\n<b>🎯 Range Forward</b> — forward a specific message ID range",
        reply_markup=InlineKeyboardMarkup(mode_buttons)
    )


@Client.on_callback_query(filters.regex(r'^fwdmode_'))
async def forward_mode(bot, query):
    _, mode, uid = query.data.split("_")
    user_id = int(uid)
    if query.from_user.id != user_id:
        return await query.answer("this isn't your setup", show_alert=True)
    setup = getattr(temp, 'FWD_SETUP', {}).get(user_id)
    if not setup:
        return await query.answer("session expired, run /forward again", show_alert=True)
    await query.message.delete()
    chat_id = setup["chat_id"]
    title = setup["title"]
    toid = setup["toid"]
    to_title = setup["to_title"]
    thread_id = setup.get("thread_id")
    _bot = setup["_bot"]

    if mode == "latest":
        try:
            last_msg = await bot.get_chat_history(chat_id, limit=1).__anext__()
            last_msg_id = last_msg.id
        except Exception as e:
            return await query.message.reply_text(f"<b>Could not read source:</b> {e}")
        skip = 0
    else:
        first_msg = await bot.ask(user_id, "<b>❪ RANGE FORWARD ❫\n\nSend the FIRST message link/ID of the range (send the message forwarded from source, or its link).\n/cancel - cancel this process</b>")
        if first_msg.text and first_msg.text.startswith('/'):
            return await first_msg.reply_text(Script.CANCEL)
        skip = await _extract_msg_id(first_msg, chat_id)
        if skip is None:
            return await first_msg.reply_text("<b>Invalid message reference</b>")

        last_msg = await bot.ask(user_id, "<b>❪ RANGE FORWARD ❫\n\nNow send the LAST message link/ID of the range.\n/cancel - cancel this process</b>")
        if last_msg.text and last_msg.text.startswith('/'):
            return await last_msg.reply_text(Script.CANCEL)
        last_msg_id = await _extract_msg_id(last_msg, chat_id)
        if last_msg_id is None:
            return await last_msg.reply_text("<b>Invalid message reference</b>")

    skip_ask = await bot.ask(user_id, Script.SKIP_MSG) if mode == "latest" else None
    if skip_ask is not None:
        if skip_ask.text.startswith('/'):
            return await skip_ask.reply_text(Script.CANCEL)
        skip = int(skip_ask.text)
        forward_id = f"{user_id}-{skip_ask.id}"
    else:
        forward_id = f"{user_id}-{last_msg.id}"

    buttons = [[
        InlineKeyboardButton('Yes', callback_data=f"start_public_{forward_id}"),
        InlineKeyboardButton('No', callback_data="close_btn")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(
        user_id,
        text=Script.DOUBLE_CHECK.format(botname=_bot['name'], botuname=_bot['username'], from_chat=title, to_chat=to_title, skip=skip),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
    STS(forward_id).store(chat_id, toid, int(skip), int(last_msg_id), thread_id)
    getattr(temp, 'FWD_SETUP', {}).pop(user_id, None)


async def _extract_msg_id(msg, expected_chat_id):
    """Accepts a t.me link or a forwarded message and returns its message id."""
    if msg.text and not msg.forward_date:
        regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(msg.text.replace("?single", ""))
        if not match:
            return None
        return int(match.group(5))
    elif msg.forward_from_chat and msg.forward_from_chat.type in [enums.ChatType.CHANNEL, 'supergroup']:
        return msg.forward_from_message_id
    return None

