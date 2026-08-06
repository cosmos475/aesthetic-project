import os
from config import Config

class  Script(object):
  START_TXT = """<b>ʜɪ {}
  
ɪ'ᴍ ᴀ ᴀᴅᴠᴀɴᴄᴇᴅ ꜰᴏʀᴡᴀʀᴅ ʙᴏᴛ
ɪ ᴄᴀɴ ꜰᴏʀᴡᴀʀᴅ ᴀʟʟ ᴍᴇssᴀɢᴇ ꜰʀᴏᴍ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴀɴᴏᴛʜᴇʀ ᴄʜᴀɴɴᴇʟ</b>

**ᴄʟɪᴄᴋ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴋɴᴏᴡ ᴍᴏʀᴇ ᴀʙᴏᴜᴛ ᴍᴇ**"""
  HELP_TXT = """<b><u>☀️ Help</u></b>

<b>📚 Available commands:</b>
⚛ /start - check I'm alive
⚛ /forward - forward messages
⚛ /settings - configure your settings
⚛ /sourcesetup - set up your source
⚛ /destinationsetup - set up your destination
⚛ /unequify - delete duplicate media messages in chats
⚛ /stop - stop your ongoing tasks
⚛ /reset - reset your settings

Tap a guide below to learn more 👇"""

  ABOUT_BOT_TXT = """<b><u>📖 About This Bot</u></b>

I'm an advanced forwarding bot. I forward messages from a source (channel, group, or supergroup topic) to a destination, using your own added Bot or Userbot to do the actual work.

<b>📚 Commands:</b>
⚛ /start — check I'm alive
⚛ /forward — start a forward job
⚛ /settings — manage bots, captions, buttons, filters & more
⚛ /sourcesetup — configure where messages come from
⚛ /destinationsetup — configure where messages go
⚛ /unequify — delete duplicate media messages in a chat
⚛ /stop — stop an ongoing forward/task
⚛ /reset — reset your settings

<b>✨ Features:</b>
► Forward from a public channel with zero admin setup
► Custom captions & buttons
► Skip duplicate messages
► Filter by message type"""

  BOT_SETUP_GUIDE_TXT = """<b><u>🤖 Bot &amp; Userbot Setup Guide</u></b>

You need at least one Bot or Userbot added under /settings → 🤖 Bots before forwarding will work — this is what actually reads and sends the messages.

<b>➕ Adding your own Bot:</b>
1️⃣ Message @BotFather → /newbot → follow the steps
2️⃣ Copy the token it gives you
3️⃣ Settings → Bots → Add Bot → paste the token (or just forward BotFather's token message)

<b>➕ Adding a Userbot:</b>
1️⃣ Settings → Bots → Add User Bot
2️⃣ Send your phone number with country code (e.g. +13124562345)
3️⃣ Enter the OTP you receive, spaced out digit by digit (e.g. 1 2 3 4 5)
4️⃣ If you have Two-Step Verification enabled, send that password when asked

<b>🤔 Which one do I need?</b>
► A Bot is enough for channels and any group/topic where you can make it admin
► A Userbot is needed for a public Normal Group/Topic where you can't (or don't want to) add any bot as admin

⚠️ Userbots carry a small risk of account restriction from Telegram — use an account you're comfortable with."""

  SOURCE_SETUP_GUIDE_TXT = """<b><u>📥 Source Setup Guide</u></b>

Open Source Setup, choose a type, then follow whichever applies:

<b>📡 Channel</b>
Forward a message from the channel to this bot, or paste its message link.
► Public channel: no admin needed at all
► Private channel: your Bot/Userbot must be admin there first

<b>👥 Normal Group / 🗂 Supergroup Topic</b>
► Private group: add this bot as admin, then send /setsource inside the group (inside the topic, for topics)
► Public group: paste any message link from that group instead — no admin needed for setup, but a Userbot is required to actually forward from it later

/sourcesetup any time to view, change, or remove your current source."""

  DESTINATION_SETUP_GUIDE_TXT = """<b><u>📤 Destination Setup Guide</u></b>

Open Destination Setup, choose a type, then follow whichever applies:

<b>📡 Channel</b>
Forward a message from the channel to this bot, or paste its message link.
Your Bot/Userbot must always be admin in the destination channel — this can't be skipped, since messages need to actually be sent there.

<b>👥 Normal Group / 🗂 Supergroup Topic</b>
Add this bot as admin in the destination group, then send /setdestination inside it (inside the topic, for topics).

/destinationsetup any time to view, change, or remove your current destination."""

  SETTINGS_GUIDE_TXT = """<b><u>⚙️ Settings Guide</u></b>

Open /settings to find:

⚛ <b>🤖 Bots</b> — add, remove, or switch between your added Bots/Userbots
⚛ <b>🖋 Caption</b> — set a custom caption for forwarded messages
⚛ <b>🔘 Button</b> — attach a custom inline button
⚛ <b>🕵 Filters</b> — choose which message types get forwarded (photo, video, etc.)
⚛ <b>🗃 MongoDB</b> — connect your own database
⚛ <b>🧪 Extra Settings</b> — additional fine-tuning options
⚛ <b>🏢 Branding</b> — customize the developer/branding link shown on /start"""

  ADMIN_REQUIREMENTS_TXT = """<b><u>🛡️ Where Admin Is Needed</u></b>

<b>📡 Channel (source)</b>
► Public — not needed
► Private — Bot/Userbot must be admin

<b>📡 Channel (destination)</b>
► Always needed (public or private)

<b>👥 Normal Group / 🗂 Topic (source)</b>
► Public — not needed for setup, but forwarding needs a Userbot
► Private — Bot/Userbot must be admin

<b>👥 Normal Group / 🗂 Topic (destination)</b>
► Always needed (public or private)

💡 When in doubt: if forwarding fails with a "may be private" error, add your Bot/Userbot as admin in that chat, or switch to a Userbot for public groups/topics."""

  HOW_USE_TXT = """<b><u>⚠️ Before Forwarding:</b></u>
<b>► __add a bot or userbot__
► __add atleast one to channel__ `(your bot/userbot must be admin in there)`
► __You can add chats or bots by using /settings__
► __if the **From Channel** is private your userbot must be member in there or your bot must need admin permission in there also__
► __Then use /forward to forward messages__</b>"""
  
  ABOUT_TXT = """<b>
╔════❰ ғᴏʀᴡᴀʀᴅ ʙᴏᴛ ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼📃ʙᴏᴛ : Forward Bot
║┣⪼📡Hᴏsᴛᴇᴅ ᴏɴ : Sᴜᴘᴇʀ Fᴀsᴛ
║┣⪼🗣️Lᴀɴɢᴜᴀɢᴇ : Pʏᴛʜᴏɴ3
║┣⪼📚Lɪʙʀᴀʀʏ : Pʏʀᴏɢʀᴀᴍ Gᴀᴛʜᴇʀ 2.11.0 
║┣⪼🗒️Vᴇʀsɪᴏɴ : 0.18.3
║╰━━━━━━━━━━━━━━━➣
╚══════════════════❍⊱❁۪۪
</b>"""
  STATUS_TXT = """
╔════❰ ʙᴏᴛ sᴛᴀᴛᴜs  ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼**⏳ ʙᴏᴛ ᴜᴘᴛɪᴍᴇ:**`{}`
║┃
║┣⪼**👱 Tᴏᴛᴀʟ Usᴇʀs:** `{}`
║┃
║┣⪼**🤖 Tᴏᴛᴀʟ Bᴏᴛ:** `{}`
║┃
║┣⪼**🔃 Fᴏʀᴡᴀʀᴅɪɴɢs:** `{}`
║┃
║╰━━━━━━━━━━━━━━━➣
╚══════════════════❍⊱❁۪۪
"""
  FROM_MSG = "<b>❪ SET SOURCE CHAT ❫\n\nForward the last message or last message link of source chat.\n/cancel - cancel this process</b>"
  TO_MSG = "<b>❪ CHOOSE TARGET CHAT ❫\n\nChoose your target chat from the given buttons.\n/cancel - Cancel this process</b>"
  SKIP_MSG = "<b>❪ SET MESSAGE SKIPING NUMBER ❫</b>\n\n<b>Skip the message as much as you enter the number and the rest of the message will be forwarded\nDefault Skip Number =</b> <code>0</code>\n<code>eg: You enter 0 = 0 message skiped\n You enter 5 = 5 message skiped</code>\n/cancel <b>- cancel this process</b>"
  CANCEL = "<b>Process Cancelled Succefully !</b>"
  BOT_DETAILS = "<b><u>📄 BOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ BOT ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}"
  USER_DETAILS = "<b><u>📄 USERBOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ USER ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}"  
         
  TEXT = """
╔════❰ ғᴏʀᴡᴀʀᴅ sᴛᴀᴛᴜs  ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼<b>📍 Cᴜʀʀᴇɴᴛ/Tᴏᴛᴀʟ :</b> <code>{}</code>/<code>{}</code>
║┃
║┣⪼<b>✅ Fᴏʀᴡᴀʀᴅᴇᴅ :</b> <code>{}</code>
║┃
║┣⪼<b>👥 Dᴜᴘʟɪᴄᴀᴛᴇ :</b> <code>{}</code>
║┃
║┣⪼<b>❌ Fᴀɪʟᴇᴅ :</b> <code>{}</code>
║┃
║┣⪼<b>🔁 Fɪʟᴛᴇʀᴇᴅ :</b> <code>{}</code>
║┃
║┣⪼<b>📊 Sᴛᴀᴛᴜs:</b> <code>{}</code>
║┃
║┣⪼<b>𖨠 Pᴇʀᴄᴇɴᴛᴀɢᴇ:</b> <code>{}</code> %
║┃
║┣⪼<b>⏱ ETA:</b> <code>{}</code>
║╰━━━━━━━━━━━━━━━➣ 
╚════❰ {} ❱══❍⊱❁۪۪
"""
  DUPLICATE_TEXT = """
╔════❰ ᴜɴᴇǫᴜɪғʏ sᴛᴀᴛᴜs ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼ <b>ғᴇᴛᴄʜᴇᴅ ғɪʟᴇs:</b> <code>{}</code>
║┃
║┣⪼ <b>ᴅᴜᴘʟɪᴄᴀᴛᴇ ᴅᴇʟᴇᴛᴇᴅ:</b> <code>{}</code> 
║╰━━━━━━━━━━━━━━━➣
╚════❰ {} ❱══❍⊱❁۪۪
"""
  DOUBLE_CHECK = """<b><u>DOUBLE CHECKING ⚠️</b></u>
<code>Before forwarding the messages Click the Yes button only after checking the following</code>

<b>★ YOUR BOT:</b> [{botname}](t.me/{botuname})
<b>★ FROM CHANNEL:</b> `{from_chat}`
<b>★ TO CHANNEL:</b> `{to_chat}`
<b>★ SKIP MESSAGES:</b> `{skip}`

<i>° [{botname}](t.me/{botuname}) must be admin in **TARGET CHAT**</i> (`{to_chat}`)
<i>° If the **SOURCE CHAT** is private your userbot must be member or your bot must be admin in there also</b></i>

<b>If the above is checked then the yes button can be clicked</b>"""
  
SETTINGS_TXT = """<b>change your settings as your wish</b>"""
