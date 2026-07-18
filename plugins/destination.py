from database import db
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TYPE_LABEL = {"channel": "📢 Channel", "group": "👥 Group", "topic": "🧵 Topic"}


def _menu_buttons():
    buttons = [[
        InlineKeyboardButton('✚ Add Channel / Group', callback_data="dest#add")
    ],[
        InlineKeyboardButton('📋 Saved Destinations', callback_data="dest#list")
    ],[
        InlineKeyboardButton('⫷ Back', callback_data="back")
    ]]
    return InlineKeyboardMarkup(buttons)


@Client.on_message(filters.private & filters.command(["destinationsetup"]))
async def destination_setup_cmd(client, message):
    await message.reply_text(
        "<b><u>DESTINATION SETUP</u></b>\n\n"
        "<b>Manage where messages get forwarded to.</b>\n\n"
        "<b>• Channel</b> — add your bot as admin, then forward a message here\n"
        "<b>• Normal Group</b> — add your bot as admin, then forward a message here\n"
        "<b>• Topic-wise Group</b> — add your bot as admin in the forum, then run /setdestination inside the desired topic",
        reply_markup=_menu_buttons()
    )


@Client.on_message(filters.command("setdestination") & (filters.group | filters.channel))
async def set_destination_topic(client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    title = message.chat.title
    username = ("@" + message.chat.username) if message.chat.username else "private"

    if message.chat.is_forum and message.message_thread_id:
        thread_id = message.message_thread_id
        added = await db.add_channel(user_id, chat_id, title, username, type="topic", thread_id=thread_id)
        return await message.reply_text(
            f"✅ <b>Destination topic saved!</b>\n\n"
            f"🏷 Group: {title}\n"
            f"🆔 Group ID: <code>{chat_id}</code>\n"
            f"📌 Thread ID: <code>{thread_id}</code>\n\n"
            "You can now use /forward in private chat to start forwarding."
            if added else "<b>This topic is already added</b>"
        )

    added = await db.add_channel(user_id, chat_id, title, username, type="group")
    await message.reply_text(
        f"✅ <b>Destination group saved!</b>\n\n"
        f"🏷 Group: {title}\n"
        f"🆔 Group ID: <code>{chat_id}</code>\n\n"
        "You can now use /forward in private chat to start forwarding."
        if added else "<b>This group is already added</b>"
    )


@Client.on_callback_query(filters.regex(r'^dest#'))
async def destination_query(bot, query):
    user_id = query.from_user.id
    _, action = query.data.split("#", 1)

    if action == "menu":
        return await query.message.edit_text(
            "<b><u>DESTINATION SETUP</u></b>\n\n<b>Manage where messages get forwarded to.</b>",
            reply_markup=_menu_buttons())

    if action == "list":
        destinations = await db.get_user_channels(user_id)
        buttons = []
        for d in destinations:
            label = TYPE_LABEL.get(d.get("type", "channel"), "📢 Channel")
            buttons.append([InlineKeyboardButton(f"{label} {d['title']}",
                            callback_data=f"dest#view_{d['chat_id']}")])
        buttons.append([InlineKeyboardButton('back', callback_data="dest#menu")])
        text = "<b><u>SAVED DESTINATIONS</u></b>" if destinations else "<b>No destinations saved yet.</b>"
        return await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    if action == "add":
        await query.message.delete()
        msg = await bot.ask(
            chat_id=user_id,
            text="<b>❪ ADD DESTINATION ❫\n\nForward a message from the target Channel or Normal Group.\nFor Topic-wise Groups, use /setdestination inside the topic instead.\n\n/cancel - cancel this process</b>"
        )
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton('back', callback_data="dest#menu")]])
        if msg.text == "/cancel":
            return await msg.reply_text("<b>process canceled</b>", reply_markup=back_btn)
        elif not msg.forward_date:
            return await msg.reply_text("<b>This is not a forwarded message</b>", reply_markup=back_btn)
        chat_id = msg.forward_from_chat.id
        title = msg.forward_from_chat.title
        username = msg.forward_from_chat.username
        username = "@" + username if username else "private"
        chat_type = "group" if msg.forward_from_chat.type in ("group", "supergroup") else "channel"
        added = await db.add_channel(user_id, chat_id, title, username, type=chat_type)
        await msg.reply_text(
            "<b>Successfully added</b>" if added else "<b>This destination already added</b>",
            reply_markup=back_btn)
        return

    if action.startswith("view_"):
        chat_id = action.split("_", 1)[1]
        d = await db.get_channel_details(user_id, chat_id)
        label = TYPE_LABEL.get(d.get("type", "channel"), "📢 Channel")
        text = (
            f"<b><u>DESTINATION DETAILS</u></b>\n\n"
            f"<b>Type:</b> {label}\n"
            f"<b>Title:</b> <code>{d['title']}</code>\n"
            f"<b>Chat ID:</b> <code>{d['chat_id']}</code>\n"
            f"<b>Username:</b> {d['username']}"
        )
        if d.get("thread_id"):
            text += f"\n<b>Topic ID:</b> <code>{d['thread_id']}</code>"
        buttons = [[
            InlineKeyboardButton('❌ Remove', callback_data=f"dest#remove_{chat_id}")
        ],[
            InlineKeyboardButton('back', callback_data="dest#list")
        ]]
        return await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    if action.startswith("remove_"):
        chat_id = action.split("_", 1)[1]
        await db.remove_channel(user_id, chat_id)
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton('back', callback_data="dest#list")]])
        return await query.message.edit_text("<b>successfully removed</b>", reply_markup=buttons)
