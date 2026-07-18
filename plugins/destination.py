from database import db
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TYPE_LABEL = {"channel": "📡 Channel", "group": "👥 Normal Group", "topic": "🗂 Supergroup Topic"}


# === TEMP DEBUG LOGGING — remove after diagnosis ===
@Client.on_message(filters.group | filters.channel, group=-1)
async def _debug_log_all_updates(client, message):
    print(
        f"[RAW] chat_id={message.chat.id} chat_type={message.chat.type} "
        f"thread_id={getattr(message, 'message_thread_id', 'NO_ATTR')} "
        f"text={message.text!r} "
        f"is_topic_message={getattr(message, 'is_topic_message', 'NO_ATTR')} "
        f"reply_to_top_message_id={getattr(message, 'reply_to_top_message_id', 'NO_ATTR')}"
    )
    reached = filters.command("setdestination")
    matched = await reached(client, message)
    print(f"[RAW] would_match_setdestination_filter={matched}")
# === END TEMP DEBUG LOGGING ===


def _type_menu_buttons():
    buttons = [[
        InlineKeyboardButton('📡 Channel', callback_data="dest#channel")
    ],[
        InlineKeyboardButton('👥 Normal Group', callback_data="dest#group")
    ],[
        InlineKeyboardButton('🗂 Supergroup Topics', callback_data="dest#topic")
    ],[
        InlineKeyboardButton('⬅ Back', callback_data="back")
    ]]
    return InlineKeyboardMarkup(buttons)


async def _destination_text(user_id):
    dst = await db.get_destination(user_id)
    if not dst:
        return "📦 <b>Set Destination</b>\n\n<b>No destination configured yet.</b>\n\nChoose the type of destination:"
    label = TYPE_LABEL.get(dst.get("type", "channel"), "📡 Channel")
    text = (
        f"📦 <b>Set Destination</b>\n\n"
        f"<b>Active destination:</b> {label}\n"
        f"<b>Title:</b> <code>{dst['title']}</code>\n"
        f"<b>Chat ID:</b> <code>{dst['chat_id']}</code>"
    )
    if dst.get("thread_id"):
        text += f"\n<b>Thread ID:</b> <code>{dst['thread_id']}</code>"
    text += "\n\nChoose the type of destination to change it:"
    return text


@Client.on_message(filters.private & filters.command(["destinationsetup"]))
async def destination_setup_cmd(client, message):
    text = await _destination_text(message.from_user.id)
    await message.reply_text(text, reply_markup=_type_menu_buttons())


@Client.on_callback_query(filters.regex(r'^dest#'))
async def destination_query(bot, query):
    user_id = query.from_user.id
    _, action = query.data.split("#", 1)

    if action == "menu":
        text = await _destination_text(user_id)
        return await query.message.edit_text(text, reply_markup=_type_menu_buttons())

    if action == "channel":
        await query.message.delete()
        msg = await bot.ask(
            chat_id=user_id,
            text="<b>❪ SET CHANNEL DESTINATION ❫\n\nForward a message from the destination channel.\n\n/cancel - cancel this process</b>"
        )
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton('back', callback_data="dest#menu")]])
        if msg.text == "/cancel":
            return await msg.reply_text("<b>process canceled</b>", reply_markup=back_btn)
        if not msg.forward_date or not msg.forward_from_chat or msg.forward_from_chat.type != enums.ChatType.CHANNEL:
            return await msg.reply_text("<b>This is not a forwarded message from a channel</b>", reply_markup=back_btn)
        chat_id = msg.forward_from_chat.id
        title = msg.forward_from_chat.title
        username = msg.forward_from_chat.username
        username = "@" + username if username else "private"
        await db.set_destination(user_id, chat_id, title, username, type="channel")
        return await msg.reply_text(
            f"✅ <b>Destination channel saved!</b>\n\n🏷 Channel: {title}\n🆔 Channel ID: <code>{chat_id}</code>\n\nYou can now use /forward in private chat.",
            reply_markup=back_btn)

    if action == "group":
        return await query.message.edit_text(
            "<b>❪ NORMAL GROUP DESTINATION ❫</b>\n\n"
            "1. Add this bot as admin in the destination group.\n"
            "2. Make sure Anonymous Admin mode is OFF.\n"
            "3. Send <code>/setdestination</code> inside that group.\n\n"
            "This will save it as your active destination.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('back', callback_data="dest#menu")]])
        )

    if action == "topic":
        await db.set_capture_mode(user_id, True)
        return await query.message.edit_text(
            "🎯 <b>Topic Capture Mode Enabled</b>\n\n"
            "1. Add this bot as admin in the destination supergroup.\n"
            "2. Make sure Anonymous Admin mode is OFF.\n"
            "3. Open the desired topic and send <code>/setdestination</code> inside it.\n\n"
            "⏳ This mode expires in <b>10 minutes</b>.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('back', callback_data="dest#menu")]])
        )


@Client.on_message(filters.command("setdestination") & (filters.group | filters.channel))
async def set_destination_topic(client, message):
    print(f"[SETDEST] chat_id={message.chat.id} type={message.chat.type} thread_id={message.message_thread_id}")
    user_id = message.from_user.id
    chat_id = message.chat.id
    title = message.chat.title
    username = ("@" + message.chat.username) if message.chat.username else "private"

    if message.message_thread_id:
        if not await db.is_capture_active(user_id):
            return await message.reply(
                "⚠️ Topic capture mode is not active.\n\n"
                "Go to bot private chat, open Destination Setup → Supergroup Topics, "
                "then come back and send /setdestination here."
            )
        thread_id = message.message_thread_id
        await db.set_destination(user_id, chat_id, title, username, type="topic", thread_id=thread_id)
        await db.set_capture_mode(user_id, False)
        return await message.reply_text(
            f"✅ <b>Destination topic saved!</b>\n\n"
            f"🏷 Group: {title}\n"
            f"🆔 Group ID: <code>{chat_id}</code>\n"
            f"📌 Thread ID: <code>{thread_id}</code>\n\n"
            "You can now use /forward in private chat to start forwarding."
        )

    await db.set_destination(user_id, chat_id, title, username, type="group")
    await message.reply_text(
        f"✅ <b>Destination group saved!</b>\n\n"
        f"🏷 Group: {title}\n"
        f"🆔 Group ID: <code>{chat_id}</code>\n\n"
        "You can now use /forward in private chat to start forwarding."
  )
  
