import time
from database import db
from pyrogram import Client, filters, enums
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate as PrivateChat
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified, ChannelPrivate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import re

LINK_REGEX = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")

TYPE_LABEL = {"channel": "📡 Channel", "group": "👥 Normal Group", "topic": "🗂 Supergroup Topic"}

# Same forum-fix as destination.py: pyrofork assigns ChatType.FORUM (not GROUP/SUPERGROUP)
# to supergroups that have Topics enabled, so filters.group alone would silently drop
# updates from forum-enabled supergroups. any_group_or_forum covers all three.
any_group_or_forum = filters.group | filters.create(
    lambda _, __, m: bool(m.chat and m.chat.type == enums.ChatType.FORUM)
)


def _menu_buttons(has_source):
    buttons = []
    if has_source:
        buttons.append([InlineKeyboardButton('👀 View Source', callback_data="source#view")])
        buttons.append([InlineKeyboardButton('♻️ Change Source', callback_data="source#set")])
        buttons.append([InlineKeyboardButton('❌ Remove Source', callback_data="source#remove")])
    else:
        buttons.append([InlineKeyboardButton('✚ Set Source', callback_data="source#set")])
    buttons.append([InlineKeyboardButton('⫷ Back', callback_data="back")])
    return InlineKeyboardMarkup(buttons)


def _type_menu_buttons():
    buttons = [[
        InlineKeyboardButton('📡 Channel', callback_data="srctype#channel")
    ],[
        InlineKeyboardButton('👥 Normal Group', callback_data="srctype#group")
    ],[
        InlineKeyboardButton('🗂 Supergroup Topics', callback_data="srctype#topic")
    ],[
        InlineKeyboardButton('⬅ Back', callback_data="source#menu")
    ]]
    return InlineKeyboardMarkup(buttons)


async def _source_screen(user_id):
    src = await db.get_source(user_id)
    if not src:
        return "<b><u>SOURCE SETUP</u></b>\n\n<b>No source configured yet.</b>\n\nSet a source channel or group to forward messages from.", _menu_buttons(False)
    label = TYPE_LABEL.get(src.get("type", "channel"), "📡 Channel")
    text = (
        f"<b><u>SOURCE SETUP</u></b>\n\n"
        f"<b>Type:</b> {label}\n"
        f"<b>Title:</b> <code>{src['title']}</code>\n"
        f"<b>Username:</b> {src.get('username') or 'private'}\n"
        f"<b>Chat ID:</b> <code>{src['chat_id']}</code>"
    )
    if src.get("thread_id"):
        text += f"\n<b>Thread ID:</b> <code>{src['thread_id']}</code>"
    return text, _menu_buttons(True)


@Client.on_message(filters.private & filters.command(["sourcesetup"]))
async def source_setup_cmd(client, message):
    text, buttons = await _source_screen(message.from_user.id)
    await message.reply_text(text, reply_markup=buttons)


@Client.on_callback_query(filters.regex(r'^source#'))
async def source_query(bot, query):
    user_id = query.from_user.id
    _, action = query.data.split("#", 1)

    if action == "menu":
        text, buttons = await _source_screen(user_id)
        return await query.message.edit_text(text, reply_markup=buttons)

    if action == "view":
        return await source_status(bot, query)

    if action == "set":
        return await query.message.edit_text(
            "📢 <b>Set Source</b>\n\nChoose the type of source:",
            reply_markup=_type_menu_buttons()
        )

    if action == "remove":
        await db.remove_source(user_id)
        text, buttons = await _source_screen(user_id)
        return await query.message.edit_text(text, reply_markup=buttons)


@Client.on_callback_query(filters.regex(r'^srctype#'))
async def source_type_query(bot, query):
    user_id = query.from_user.id
    _, action = query.data.split("#", 1)
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton('back', callback_data="source#menu")]])

    if action == "channel":
        await query.message.delete()
        msg = await bot.ask(
            user_id,
            "<b>❪ SET SOURCE ❫\n\nForward the last message from the source channel, or send its message link.\nIf the source is private, add your bot/userbot as admin there first.\n\n/cancel - cancel this process</b>"
        )
        if msg.text and msg.text.startswith('/'):
            text, buttons = await _source_screen(user_id)
            return await msg.reply_text("<b>process canceled</b>", reply_markup=buttons)

        chat_id = None
        if msg.text and not msg.forward_date:
            match = LINK_REGEX.match(msg.text.replace("?single", ""))
            if not match:
                text, buttons = await _source_screen(user_id)
                return await msg.reply_text("<b>Invalid link</b>", reply_markup=buttons)
            raw_id = match.group(4)
            chat_id = int("-100" + raw_id) if raw_id.isnumeric() else raw_id
        elif msg.forward_from_chat and msg.forward_from_chat.type in [enums.ChatType.CHANNEL, 'supergroup']:
            chat_id = msg.forward_from_chat.username or msg.forward_from_chat.id
        else:
            text, buttons = await _source_screen(user_id)
            return await msg.reply_text("<b>invalid !</b>", reply_markup=buttons)

        try:
            chat = await bot.get_chat(chat_id)
            title = chat.title
            username = ("@" + chat.username) if chat.username else "private"
        except (PrivateChat, ChannelPrivate, ChannelInvalid):
            title = msg.forward_from_chat.title if msg.forward_date else "private"
            username = "private"
            chat_id = chat_id if msg.text else msg.forward_from_chat.id
        except (UsernameInvalid, UsernameNotModified):
            text, buttons = await _source_screen(user_id)
            return await msg.reply_text("<b>Invalid link specified.</b>", reply_markup=buttons)
        except Exception as e:
            text, buttons = await _source_screen(user_id)
            return await msg.reply_text(f"<b>Error:</b> {e}", reply_markup=buttons)

        await db.set_source(user_id, chat_id, title, username, type="channel")
        text, buttons = await _source_screen(user_id)
        return await msg.reply_text("<b>Source channel saved successfully</b>", reply_markup=buttons)

    if action == "group":
        await db.set_capture_mode(user_id, True, mode="source")
        return await query.message.edit_text(
            "<b>❪ NORMAL GROUP SOURCE ❫</b>\n\n"
            "1. Add this bot as admin in the source group.\n"
            "2. Make sure Anonymous Admin mode is OFF.\n"
            "3. Send <code>/setsource</code> inside that group.\n\n"
            "⏳ This mode expires in <b>10 minutes</b>.",
            reply_markup=back_btn
        )

    if action == "topic":
        await db.set_capture_mode(user_id, True, mode="source")
        return await query.message.edit_text(
            "🎯 <b>Source Topic Capture Mode Enabled</b>\n\n"
            "1. Add this bot as admin in the source supergroup.\n"
            "2. Make sure Anonymous Admin mode is OFF.\n"
            "3. Open the desired topic and send <code>/setsource</code> inside it.\n\n"
            "⏳ This mode expires in <b>10 minutes</b>.",
            reply_markup=back_btn
        )


@Client.on_message(filters.command("setsource") & (any_group_or_forum | filters.channel))
async def set_source_group(client, message):
    print(f"[SETSRC] chat_id={message.chat.id} type={message.chat.type} thread_id={message.message_thread_id}")
    user_id = message.from_user.id
    chat_id = message.chat.id
    title = message.chat.title
    username = ("@" + message.chat.username) if message.chat.username else "private"
    thread_id = message.message_thread_id

    try:
        if not await db.is_capture_active(user_id, mode="source"):
            return await client.send_message(
                chat_id,
                "⚠️ Source capture mode is not active.\n\n"
                "Go to bot private chat, open Source Setup → Normal Group/Supergroup Topics, "
                "then come back and send /setsource here.",
                message_thread_id=thread_id,
            )

        if thread_id:
            await db.set_source(user_id, chat_id, title, username, type="topic", thread_id=thread_id)
            await db.set_capture_mode(user_id, False, mode="source")
            return await client.send_message(
                chat_id,
                f"✅ <b>Source topic saved!</b>\n\n"
                f"🏷 Group: {title}\n"
                f"🆔 Group ID: <code>{chat_id}</code>\n"
                f"📌 Thread ID: <code>{thread_id}</code>\n\n"
                "You can now use /forward in private chat to start forwarding.",
                message_thread_id=thread_id,
            )

        await db.set_source(user_id, chat_id, title, username, type="group")
        await db.set_capture_mode(user_id, False, mode="source")
        await client.send_message(
            chat_id,
            f"✅ <b>Source group saved!</b>\n\n"
            f"🏷 Group: {title}\n"
            f"🆔 Group ID: <code>{chat_id}</code>\n\n"
            "You can now use /forward in private chat to start forwarding.",
        )
    except Exception as e:
        print(f"[SETSRC][ERROR] {type(e).__name__}: {e}")
        try:
            await client.send_message(chat_id, f"⚠️ Error saving source: <code>{e}</code>", message_thread_id=thread_id)
        except Exception as e2:
            print(f"[SETSRC][ERROR-FALLBACK-FAILED] {type(e2).__name__}: {e2}")


async def source_status(bot, query):
    """On-demand (lazy) source verification -- no background polling."""
    user_id = query.from_user.id
    src = await db.get_source(user_id)
    if not src:
        text, buttons = await _source_screen(user_id)
        return await query.message.edit_text(text, reply_markup=buttons)

    status = "Alive"
    try:
        await bot.get_chat(src['chat_id'])
    except Exception:
        status = "Not Found"
    verified_at = time.time()
    await db.update_source_status(user_id, status, verified_at)

    privacy = "Private" if src.get('username') in (None, 'private') else "Public"
    label = TYPE_LABEL.get(src.get("type", "channel"), "📡 Channel")
    text = (
        f"<b><u>SOURCE INFO</u></b>\n\n"
        f"<b>Name:</b> <code>{src['title']}</code>\n"
        f"<b>Type:</b> {label}\n"
        f"<b>Privacy:</b> {privacy}\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Last Verified:</b> just now"
    )
    if src.get("thread_id"):
        text += f"\n<b>Thread ID:</b> <code>{src['thread_id']}</code>"
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton('back', callback_data="source#menu")]])
    await query.message.edit_text(text, reply_markup=buttons)
