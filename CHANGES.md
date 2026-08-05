# Changes Summary

3 files modified: `plugins/source.py`, `plugins/public.py`, `plugins/regix.py`.
No diagnostic/debug logging included — production-clean.

Private Group / Private Channel / `/setsource`-in-group flow: **untouched**, works exactly
as before.

---

## 1. `plugins/public.py` — Range Forward now accepts public links

**Problem:** The Range Forward step ("send the link of the first/last message") only
recognized private-style links (`t.me/c/<internal_id>/<msg_id>`). Any public-group or
public-channel link (`t.me/username/<msg_id>`) was rejected with "Invalid message
reference", even for a correctly-configured public source.

**Fix:**
- Added a second regex (`_MSG_LINK_RE_PUBLIC`) alongside the original private-link regex
  (kept as `_MSG_LINK_RE_PRIVATE`, unchanged) to also parse `t.me/<username>/<msg_id>` and
  `t.me/<username>/<thread_id>/<msg_id>` (topic) links.
- `_extract_msg_id()` now tries the private format first (original behavior preserved),
  and falls back to the public format if the source has a known username — verifying the
  link's username matches the configured source before accepting it.
- The source's username is now threaded through `FWD_SETUP` so this validation has what
  it needs.

**Result:** Range Forward now works for public channels, public groups, and public topics,
using either private or public link formats — while all private-link behavior is
identical to before.

---

## 2. `plugins/source.py` — Public Group/Topic source setup via link (no admin needed)

**Problem:** Setting a Normal Group or Supergroup Topic as source only worked via
`/setsource` run inside the group, which requires the bot to be an admin there. There was
no equivalent to the Channel flow's "just paste a message link" option.

**Fix:**
- Added a new parallel path (`_await_public_group_link()`) that runs alongside the
  existing `/setsource`-in-group capture mode. The instruction screen for Normal
  Group / Supergroup Topics now also explains this option.
- If the user pastes a public group/topic message link instead of running `/setsource`,
  the bot resolves the group via `get_chat()`, stores `chat_id` as the **username string**
  (not the numeric chat ID) plus `thread_id` for topics — mirroring how the Channel flow
  already works.
- Whichever method (`/setsource` in-group, or pasted link) completes first is the one
  that's saved; the other is safely ignored via an `is_capture_active()` check.
- A new topic-specific 3-segment regex (`_PUBLIC_TOPIC_LINK_REGEX`) handles
  `t.me/<username>/<thread_id>/<msg_id>` links for topic sources. The shared `LINK_REGEX`
  used by the channel/private flows is untouched.
- Private-chat links (numeric, no username) are explicitly rejected in this new path with
  a message telling the user to use admin + `/setsource` instead.

**Result:** Public Normal Group / Topic sources can now be set up by pasting a link, no
admin required — Source Setup screen correctly shows the username-based chat ID.

---

## 3. `plugins/regix.py` — Peer warm-up before fetching

**Problem:** The forward job creates a fresh Pyrogram/pyrofork `Client` per job. Calling
`get_messages()` directly on a username-based `chat_id` (e.g. after the source.py fix
above) with no prior peer resolution could raise a local `KeyError` before Pyrogram
attempted to resolve the peer at all.

**Fix:**
- Added `await client.get_chat(sts.get("FROM"))` immediately before the existing
  `get_messages()` sanity-check, in both the main forward handler and the
  restart-pending-forwards handler. This forces proper peer resolution first.
- For numeric/private chat_ids (existing private group/channel flow), this call is a
  no-op in effect — same result as before, no behavior change.

**Result:** Username-based (public) sources get a proper resolve attempt before the
fetch. Note: this does **not** override the underlying Telegram-side restriction — see
below.

---

## Known limitation (not a code bug — documented, not "fixed")

**Public Normal Groups still require either the bot to be an admin/member, or a Userbot
session, to actually forward.** This was confirmed to be a Telegram MTProto-level
restriction: bot accounts cannot resolve/read a non-broadcast Normal Group's public
username-based peer unless they're already a member — this restriction does **not**
apply to public Channels (broadcast-type), where bot accounts work fine with zero
membership, and does **not** apply to Userbot (real user account) sessions on Normal
Groups either.

So, end-to-end status:

| Source type | Setup method | Range Forward | Actual forwarding (Bot mode) | Actual forwarding (Userbot mode) |
|---|---|---|---|---|
| Public Channel | link/forward | ✅ | ✅ (always worked) | ✅ |
| Private Channel/Group | `/setsource` (admin) | ✅ | ✅ | ✅ |
| Public Normal Group/Topic | link (no admin) | ✅ | ❌ Telegram restriction | ✅ |
| Public Normal Group/Topic | `/setsource` (admin) | ✅ | ✅ | ✅ |

For public Normal Groups/Topics without admin, the bot should be used with a Userbot
session added under Settings, since a bot-token client cannot forward from a Normal Group
it isn't a member of — no code-level fix exists for this on the Bot API/MTProto side for
bot accounts.
