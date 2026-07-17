"""
messages.py
------------
All user-facing text templates for OplusSupportBot live here.
Keeping messages separate from logic makes it easy to edit wording
without touching bot code.
"""

import config

BOT_NAME = config.BOT_NAME
OWNER = config.OWNER_USERNAME
WEBSITE = config.WEBSITE_URL


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------
START_MSG = (
    f"👋 *Welcome to {BOT_NAME}!*\n\n"
    "Your trusted partner for OPPO, OnePlus & Realme unlocking services.\n\n"
    "🔹 FRP Unlock\n"
    "🔹 Flashing Tools\n"
    "🔹 Auth Services\n\n"
    "Use the buttons below or type /help to see all available commands."
)

HELP_MSG = (
    f"📖 *{BOT_NAME} — Command List*\n\n"
    "/start - Start the bot\n"
    "/help - Show this help message\n"
    "/status - Server status\n"
    "/frp - FRP unlock info\n"
    "/flash - Flash tool info\n"
    "/auth - Auth service info\n"
    "/price - Pricing info\n"
    "/contact - Contact admin\n"
    "/website - Visit our website\n"
    "/support - Supported brands\n"
    "/ping - Check bot response time\n\n"
    "*Admin Only Commands (group chats):*\n"
    "/ban - Ban a user (reply to their message)\n"
    "/unban - Unban a user (reply to their message)\n"
    "/mute - Mute a user (reply to their message)\n"
    "/unmute - Unmute a user (reply to their message)\n"
    "/warn - Warn a user (reply to their message)"
)

UNKNOWN_COMMAND_MSG = (
    "❓ Sorry, I didn't understand that command.\n"
    "Type /help to see the list of available commands."
)

# ---------------------------------------------------------------------------
# Service info
# ---------------------------------------------------------------------------
STATUS_MSG = (
    "🛡 *O+ SUPPORT CURRENT SERVER STATUS* 🛡\n\n"
    "🟢 REALME MTK 1 CLICK SERVER ON\n\n"
    "🟢 REALME O+ TOOL SERVER ON\n\n"
    "🔴 OPPO AUTH SERVER OFF\n\n"
    "🔴 ONEPLUS AUTH SERVER ONLY\n"
    "(GLOBAL | CHINA NOT SUPPORTED)\n"
    "OFF"
)

FRP_MSG = (
    "🔓 *O+ SUPPORT FRP*\n\n"
    "✅ OPPO\n"
    "✅ OnePlus\n"
    "✅ Realme"
)

FLASH_MSG = (
    "⚡ *O+ SUPPORT FLASH*\n\n"
    "Supported:\n\n"
    "• OPPO\n"
    "• OnePlus\n"
    "• Realme"
)

AUTH_MSG = (
    "🔐 *AUTH SERVICE*\n\n"
    "✅ Global Support\n"
    "❌ China Not Supported"
)

PRICE_MSG = (
    "💰 *PRICING*\n\n"
    "Prices vary depending on device model & requested service.\n\n"
    f"📩 Please contact admin {OWNER} for the latest price list."
)

CONTACT_MSG = (
    "📞 *CONTACT US*\n\n"
    f"Telegram: {OWNER}\n"
    f"Website: {WEBSITE}"
)

WEBSITE_MSG = (
    "🌐 *OUR WEBSITE*\n\n"
    f"{WEBSITE}"
)

SUPPORT_MSG = (
    "🧰 *SUPPORTED BRANDS*\n\n"
    "• OPPO\n"
    "• OnePlus\n"
    "• Realme"
)

PING_MSG = "🏓 Pong! Response time: {latency} ms"

# ---------------------------------------------------------------------------
# Group management / moderation
# ---------------------------------------------------------------------------
WELCOME_NEW_MEMBER = (
    "👋 Welcome {mention} to *{bot_name}*!\n\n"
    "Please read the pinned messages and type /help to get started.\n"
    "Enjoy your stay! 🎉"
)

INVITE_LINK_DELETED = (
    "🚫 {mention}, sharing invite links is not allowed here.\n"
    "Your message was removed."
)

SPAM_DETECTED = (
    "⚠️ {mention} has been muted for {seconds} seconds due to spamming."
)

ADMIN_ONLY_MSG = "⛔ This command can only be used by an admin."
GROUP_ONLY_MSG = "⛔ This command can only be used inside a group chat."
REPLY_REQUIRED_MSG = "⚠️ Please reply to the user's message you want to take action on."

BAN_SUCCESS_MSG = "🔨 {mention} has been *banned* from the group."
UNBAN_SUCCESS_MSG = "✅ {mention} has been *unbanned* and can rejoin the group."
MUTE_SUCCESS_MSG = "🔇 {mention} has been *muted*."
UNMUTE_SUCCESS_MSG = "🔊 {mention} has been *unmuted*."
WARN_SUCCESS_MSG = "⚠️ {mention} has been warned. ({count}/{max_count})"
WARN_KICK_MSG = "🚫 {mention} reached the maximum number of warnings and has been *removed*."

ACTION_FAILED_MSG = "❌ Could not complete that action: {error}"

# ---------------------------------------------------------------------------
# Keyword -> canned response map (used for auto-reply on plain text)
# ---------------------------------------------------------------------------
KEYWORD_RESPONSES = {
    "status": STATUS_MSG,
    "frp": FRP_MSG,
    "flash": FLASH_MSG,
    "auth": AUTH_MSG,
    "price": PRICE_MSG,
    "website": WEBSITE_MSG,
    "support": SUPPORT_MSG,
    "contact": CONTACT_MSG,
    "hello": START_MSG,
    "hi": START_MSG,
}
