# Changes — This Round

4 files: `plugins/source.py`, `plugins/public.py`, `plugins/commands.py`, `script.py` (root level).

`plugins/regix.py`, `plugins/settings.py`, `plugins/db.py`, `plugins/test.py` — **untouched**.
Private-group `/setsource` flow, `set_source_group()` handler — **untouched**.
`Script.DOUBLE_CHECK` text — **untouched**, as requested.

---

## 1. Removed "Latest Forward" (`plugins/public.py`)

- Deleted the "Choose Forward Mode" screen and the `fwdmode_` callback entirely.
- `/forward` now goes straight into the Range Forward flow (the only mode that ever
  worked correctly — Latest Forward called `get_chat_history()` directly on `chat_id`,
  which wasn't wired through the same link/username handling as Range Forward and broke
  for anything other than a plain admin-channel numeric ID).
- `forward_mode()` is now a plain function called directly from `run()`, not a callback
  handler — no button, no round-trip, same result.

## 2. Range Forward now accepts public links (`plugins/public.py`)

Carried forward from earlier in this session, reapplied here since this copy of
`public.py` didn't have it yet:

- Added `_MSG_LINK_RE_PUBLIC` alongside the existing private-link regex
  (`_MSG_LINK_RE_PRIVATE`, unchanged behavior) to also parse `t.me/<username>/<msg_id>`
  and `t.me/<username>/<thread_id>/<msg_id>` (topic) links.
- `_extract_msg_id()` tries the private format first, falls back to public format if the
  source has a known username, and validates the link's username matches the configured
  source.
- `src_username` is now threaded through `FWD_SETUP` so this validation has what it needs.

## 3. Public Group/Topic source setup — now resolves via the user's own Bot/Userbot (`plugins/source.py`)

**Root cause recap:** the link-based public-group setup path was resolving the group
via *this bot's own* client (`bot.get_chat(...)`). Telegram does not allow a plain bot
account to resolve a public Normal Group's username unless it's already a member —
this held true even during setup, not just during forwarding, so setup itself was
failing with `KeyError: 'Username not found: ...'` for any group the bot wasn't already
in.

**Fix:** `_await_public_group_link()` now calls `_get_resolver_client()` first, which:
1. Tries the user's added **Userbot** (works for public Normal Groups without membership).
2. Falls back to the user's added **Bot** (works once it's a member/admin somewhere).
3. Falls back to this bot's own client only if neither exists (so the error message is
   still meaningful rather than crashing).

The temporary client is properly `.start()`ed and `.stop()`ed around the single
`get_chat()` call. If resolution still fails, the error message now includes a hint
about adding a Userbot when the failure came from the user's own client.

- Also added topic support: a dedicated `_PUBLIC_TOPIC_LINK_REGEX` (3-segment
  `username/thread_id/msg_id`) is tried when the 2-segment format doesn't match and the
  source type is `topic` — `thread_id` gets stored correctly either way.
- `set_source_group()` (the `/setsource`-in-group handler) is **completely untouched**
  — private group/topic setup behaves exactly as before.

## 4. Updated wording — Normal Group / Topic capture-mode screens (`plugins/source.py`)

Both screens now end with a clear "if you can't make anyone admin here, add a Userbot
first, then come back" instruction instead of a vague admin-skip note, per your last
round of feedback. Wording is otherwise unchanged (numbered steps, expiry line).

## 5. New Help system (`script.py` + `plugins/commands.py`)

- New `/help` command — identical output to the existing HELP button.
- Help menu now has 6 sub-guide buttons, each ending in a **⬅️ Back to Help** button:
  - 📖 About This Bot — full command list + feature summary
  - 🤖 Bot & Userbot Setup Guide — BotFather steps, phone+OTP+2FA userbot login, when to
    use which
  - 📥 Source Setup Guide — channel/group/topic, public/private, link vs `/setsource`
  - 📤 Destination Setup Guide — same pattern
  - ⚙️ Settings Guide — one-line summary of each settings section
  - 🛡️ Where Admin Is Needed — the admin-requirement matrix as plain bullets
- Old `HOW_USE_TXT` / `how_to_use` callback left in place (unreferenced by any button
  now, but not deleted, in case anything else calls it).
- `Script.DOUBLE_CHECK` — untouched, as requested.

---

## Known limitation (unchanged, documented — not a bug)

Public Normal Groups/Topics still need **either** admin access **or** a Userbot to
actually forward — this is a Telegram-side restriction on bot accounts reading
non-broadcast group content, not something fixable in code. The Help guides and the
capture-mode screens now say this plainly instead of implying admin-free setup always
means admin-free forwarding.

| Source type | Setup (no admin) | Forwarding (no admin) |
|---|---|---|
| Public Channel | ✅ | ✅ |
| Private Channel/Group/Topic | ❌ (needs admin) | ✅ once admin |
| Public Normal Group/Topic | ✅ (via link, needs Bot/Userbot to resolve) | ❌ Bot / ✅ Userbot |
