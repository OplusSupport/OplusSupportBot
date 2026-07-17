"""
main.py
--------
Entry point for OplusSupportBot.

A production-ready python-telegram-bot (v21+) application implementing:
  - Info commands (/status, /frp, /flash, /auth, /price, /contact, /website, /support)
  - Keyword auto-reply
  - Inline keyboard navigation
  - Welcome messages for new group members
  - Invite-link deletion
  - Basic anti-spam (rate limiting -> auto mute)
  - Admin moderation commands (/ban, /unban, /mute, /unmute, /warn)
  - /ping health check

Run with:  python main.py
The bot uses long-polling, so it works out of the box on Render.com
as a "Background Worker" service (see render.yaml).
"""

import logging
import re
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
    Chat,
)
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

import config
import messages as msg

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("OplusSupportBot")

# ---------------------------------------------------------------------------
# In-memory runtime state
# ---------------------------------------------------------------------------
# NOTE: This state resets if the process restarts. For a small support bot
# this is fine; swap in Redis/Postgres later if you need persistence.
user_warnings: dict = defaultdict(int)                 # (chat_id, user_id) -> warning count
spam_tracker: dict = defaultdict(lambda: deque(maxlen=50))  # (chat_id, user_id) -> timestamps

INVITE_LINK_PATTERN = re.compile(
    r"(t\.me/joinchat|t\.me/\+|telegram\.me/joinchat|telegram\.dog/joinchat)",
    re.IGNORECASE,
)

CALLBACK_TO_MESSAGE = {
    "status": msg.STATUS_MSG,
    "frp": msg.FRP_MSG,
    "flash": msg.FLASH_MSG,
    "auth": msg.AUTH_MSG,
    "price": msg.PRICE_MSG,
    "contact": msg.CONTACT_MSG,
    "support": msg.SUPPORT_MSG,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def is_bot_admin(user_id: int) -> bool:
    """True if the user is configured as a bot-level admin via ADMIN_IDS."""
    return user_id in config.ADMIN_IDS


async def is_authorized_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Returns True if the user issuing the command is allowed to run admin
    commands: either a configured bot admin, or a Telegram group
    admin/creator of the current chat.
    """
    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None:
        return False
    if is_bot_admin(user.id):
        return True
    if chat.type == Chat.PRIVATE:
        return False
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except TelegramError as exc:
        logger.warning("Failed to check admin status: %s", exc)
        return False


def mention_html(user) -> str:
    """Build an HTML mention for a Telegram user object."""
    name = user.first_name or user.username or "there"
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🛡 Status", callback_data="status"),
            InlineKeyboardButton("🔓 FRP", callback_data="frp"),
        ],
        [
            InlineKeyboardButton("⚡ Flash", callback_data="flash"),
            InlineKeyboardButton("🔐 Auth", callback_data="auth"),
        ],
        [
            InlineKeyboardButton("💰 Price", callback_data="price"),
            InlineKeyboardButton("🧰 Support", callback_data="support"),
        ],
        [
            InlineKeyboardButton("📞 Contact", callback_data="contact"),
            InlineKeyboardButton("🌐 Website", url=config.WEBSITE_URL),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]]
    )


async def get_reply_target(update: Update):
    """Return the User object of the message being replied to, or None."""
    message = update.effective_message
    if message and message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    return None


# ---------------------------------------------------------------------------
# Basic info commands
# ---------------------------------------------------------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        msg.START_MSG,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        msg.HELP_MSG,
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    start = time.perf_counter()
    sent = await update.effective_message.reply_text("🏓 Pinging...")
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    await sent.edit_text(msg.PING_MSG.format(latency=elapsed_ms))


def _make_info_command(text: str):
    """Factory for simple text-reply commands (status/frp/flash/etc.)."""

    async def _handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard(),
        )

    return _handler


cmd_status = _make_info_command(msg.STATUS_MSG)
cmd_frp = _make_info_command(msg.FRP_MSG)
cmd_flash = _make_info_command(msg.FLASH_MSG)
cmd_auth = _make_info_command(msg.AUTH_MSG)
cmd_price = _make_info_command(msg.PRICE_MSG)
cmd_contact = _make_info_command(msg.CONTACT_MSG)
cmd_website = _make_info_command(msg.WEBSITE_MSG)
cmd_support = _make_info_command(msg.SUPPORT_MSG)


# ---------------------------------------------------------------------------
# Inline keyboard callback handler
# ---------------------------------------------------------------------------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "menu":
        await query.edit_message_text(
            msg.START_MSG,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_keyboard(),
        )
        return

    text = CALLBACK_TO_MESSAGE.get(query.data)
    if text:
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard(),
        )


# ---------------------------------------------------------------------------
# Keyword auto-reply (plain text messages, not commands)
# ---------------------------------------------------------------------------
async def keyword_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return

    text = message.text.strip().lower()
    # Only react to short, single-word style triggers to avoid false positives
    # inside longer sentences.
    cleaned = re.sub(r"[^a-z]", "", text)

    response = msg.KEYWORD_RESPONSES.get(cleaned)
    if response:
        await message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard() if cleaned not in ("hello", "hi") else main_menu_keyboard(),
        )


# ---------------------------------------------------------------------------
# Group management: welcome message
# ---------------------------------------------------------------------------
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.ENABLE_WELCOME_MESSAGE:
        return
    message = update.effective_message
    if not message or not message.new_chat_members:
        return

    for new_user in message.new_chat_members:
        if new_user.is_bot and new_user.id == context.bot.id:
            continue  # don't welcome the bot itself when added to a group
        mention = mention_html(new_user)
        text = msg.WELCOME_NEW_MEMBER.format(mention=mention, bot_name=config.BOT_NAME)
        await message.chat.send_message(text, parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# Group management: invite link deletion + anti-spam
# ---------------------------------------------------------------------------
async def moderate_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Runs on every non-command text message in group chats.
    Handles: invite-link deletion and anti-spam rate limiting.
    Keyword auto-reply is handled separately so both features can coexist.
    """
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not chat or not user or chat.type == Chat.PRIVATE:
        return
    if user.is_bot:
        return

    # Skip moderation for bot-level/group admins
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin_here = member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except TelegramError:
        is_admin_here = False
    is_admin_here = is_admin_here or is_bot_admin(user.id)

    # --- Invite link deletion -------------------------------------------------
    if config.DELETE_INVITE_LINKS and not is_admin_here and message.text:
        if INVITE_LINK_PATTERN.search(message.text):
            try:
                await message.delete()
                mention = mention_html(user)
                await chat.send_message(
                    msg.INVITE_LINK_DELETED.format(mention=mention),
                    parse_mode=ParseMode.HTML,
                )
            except TelegramError as exc:
                logger.warning("Could not delete invite-link message: %s", exc)
            return  # don't also run anti-spam counting on a deleted message

    # --- Anti-spam --------------------------------------------------------
    if config.ENABLE_ANTI_SPAM and not is_admin_here:
        key = (chat.id, user.id)
        now = time.monotonic()
        timestamps = spam_tracker[key]
        timestamps.append(now)

        # Drop timestamps outside the sliding window
        while timestamps and now - timestamps[0] > config.ANTI_SPAM_TIME_WINDOW:
            timestamps.popleft()

        if len(timestamps) > config.ANTI_SPAM_MSG_LIMIT:
            try:
                until_date = datetime.now(timezone.utc) + timedelta(
                    seconds=config.ANTI_SPAM_MUTE_SECONDS
                )
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until_date,
                )
                mention = mention_html(user)
                await chat.send_message(
                    msg.SPAM_DETECTED.format(
                        mention=mention, seconds=config.ANTI_SPAM_MUTE_SECONDS
                    ),
                    parse_mode=ParseMode.HTML,
                )
                logger.info("Muted spammer user_id=%s in chat_id=%s", user.id, chat.id)
            except TelegramError as exc:
                logger.warning("Could not mute spamming user: %s", exc)
            finally:
                timestamps.clear()


# ---------------------------------------------------------------------------
# Admin moderation commands
# ---------------------------------------------------------------------------
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        await update.effective_message.reply_text(msg.GROUP_ONLY_MSG)
        return
    if not await is_authorized_admin(update, context):
        await update.effective_message.reply_text(msg.ADMIN_ONLY_MSG)
        return
    target = await get_reply_target(update)
    if not target:
        await update.effective_message.reply_text(msg.REPLY_REQUIRED_MSG)
        return
    try:
        await context.bot.ban_chat_member(chat_id=chat.id, user_id=target.id)
        await update.effective_message.reply_text(
            msg.BAN_SUCCESS_MSG.format(mention=mention_html(target)),
            parse_mode=ParseMode.HTML,
        )
        logger.info("Admin %s banned user %s in chat %s", update.effective_user.id, target.id, chat.id)
    except TelegramError as exc:
        await update.effective_message.reply_text(msg.ACTION_FAILED_MSG.format(error=exc))


async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        await update.effective_message.reply_text(msg.GROUP_ONLY_MSG)
        return
    if not await is_authorized_admin(update, context):
        await update.effective_message.reply_text(msg.ADMIN_ONLY_MSG)
        return
    target = await get_reply_target(update)
    if not target:
        await update.effective_message.reply_text(msg.REPLY_REQUIRED_MSG)
        return
    try:
        await context.bot.unban_chat_member(chat_id=chat.id, user_id=target.id, only_if_banned=True)
        await update.effective_message.reply_text(
            msg.UNBAN_SUCCESS_MSG.format(mention=mention_html(target)),
            parse_mode=ParseMode.HTML,
        )
        logger.info("Admin %s unbanned user %s in chat %s", update.effective_user.id, target.id, chat.id)
    except TelegramError as exc:
        await update.effective_message.reply_text(msg.ACTION_FAILED_MSG.format(error=exc))


async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        await update.effective_message.reply_text(msg.GROUP_ONLY_MSG)
        return
    if not await is_authorized_admin(update, context):
        await update.effective_message.reply_text(msg.ADMIN_ONLY_MSG)
        return
    target = await get_reply_target(update)
    if not target:
        await update.effective_message.reply_text(msg.REPLY_REQUIRED_MSG)
        return
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False),
        )
        await update.effective_message.reply_text(
            msg.MUTE_SUCCESS_MSG.format(mention=mention_html(target)),
            parse_mode=ParseMode.HTML,
        )
        logger.info("Admin %s muted user %s in chat %s", update.effective_user.id, target.id, chat.id)
    except TelegramError as exc:
        await update.effective_message.reply_text(msg.ACTION_FAILED_MSG.format(error=exc))


async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        await update.effective_message.reply_text(msg.GROUP_ONLY_MSG)
        return
    if not await is_authorized_admin(update, context):
        await update.effective_message.reply_text(msg.ADMIN_ONLY_MSG)
        return
    target = await get_reply_target(update)
    if not target:
        await update.effective_message.reply_text(msg.REPLY_REQUIRED_MSG)
        return
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await update.effective_message.reply_text(
            msg.UNMUTE_SUCCESS_MSG.format(mention=mention_html(target)),
            parse_mode=ParseMode.HTML,
        )
        logger.info("Admin %s unmuted user %s in chat %s", update.effective_user.id, target.id, chat.id)
    except TelegramError as exc:
        await update.effective_message.reply_text(msg.ACTION_FAILED_MSG.format(error=exc))


async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        await update.effective_message.reply_text(msg.GROUP_ONLY_MSG)
        return
    if not await is_authorized_admin(update, context):
        await update.effective_message.reply_text(msg.ADMIN_ONLY_MSG)
        return
    target = await get_reply_target(update)
    if not target:
        await update.effective_message.reply_text(msg.REPLY_REQUIRED_MSG)
        return

    key = (chat.id, target.id)
    user_warnings[key] += 1
    count = user_warnings[key]

    if count >= config.MAX_WARNINGS:
        try:
            await context.bot.ban_chat_member(chat_id=chat.id, user_id=target.id)
            await update.effective_message.reply_text(
                msg.WARN_KICK_MSG.format(mention=mention_html(target)),
                parse_mode=ParseMode.HTML,
            )
            user_warnings[key] = 0
            logger.info(
                "User %s reached max warnings and was removed from chat %s", target.id, chat.id
            )
        except TelegramError as exc:
            await update.effective_message.reply_text(msg.ACTION_FAILED_MSG.format(error=exc))
    else:
        await update.effective_message.reply_text(
            msg.WARN_SUCCESS_MSG.format(
                mention=mention_html(target), count=count, max_count=config.MAX_WARNINGS
            ),
            parse_mode=ParseMode.HTML,
        )
        logger.info("Admin %s warned user %s (%s/%s)", update.effective_user.id, target.id, count, config.MAX_WARNINGS)


# ---------------------------------------------------------------------------
# Fallback / unknown command
# ---------------------------------------------------------------------------
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(msg.UNKNOWN_COMMAND_MSG)


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------
async def error_handler(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception while processing update: %s", context.error, exc_info=context.error)


# ---------------------------------------------------------------------------
# Application bootstrap
# ---------------------------------------------------------------------------
def build_application() -> Application:
    if not config.BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. "
            "Set it in your Render dashboard (or a local .env file) before starting the bot."
        )

    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # --- Info commands ---
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("frp", cmd_frp))
    application.add_handler(CommandHandler("flash", cmd_flash))
    application.add_handler(CommandHandler("auth", cmd_auth))
    application.add_handler(CommandHandler("price", cmd_price))
    application.add_handler(CommandHandler("contact", cmd_contact))
    application.add_handler(CommandHandler("website", cmd_website))
    application.add_handler(CommandHandler("support", cmd_support))
    application.add_handler(CommandHandler("ping", cmd_ping))

    # --- Admin commands ---
    application.add_handler(CommandHandler("ban", cmd_ban))
    application.add_handler(CommandHandler("unban", cmd_unban))
    application.add_handler(CommandHandler("mute", cmd_mute))
    application.add_handler(CommandHandler("unmute", cmd_unmute))
    application.add_handler(CommandHandler("warn", cmd_warn))

    # --- Inline keyboard callbacks ---
    application.add_handler(CallbackQueryHandler(button_callback))

    # --- New chat member welcome ---
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member)
    )

    # --- Group moderation (invite links + anti-spam) runs first ---
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            moderate_group_message,
        ),
        group=0,
    )

    # --- Keyword auto-reply runs after moderation, in all chat types ---
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_auto_reply),
        group=1,
    )

    # --- Unknown command fallback ---
    # Added last, in the SAME group (0) as the known CommandHandlers above.
    # PTB only runs the first matching handler within a given group, so this
    # only fires when none of the specific /command handlers already matched.
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command), group=0)

    application.add_error_handler(error_handler)

    return application


def main() -> None:
    logger.info("Starting %s ...", config.BOT_NAME)
    application = build_application()
    logger.info("Bot is polling for updates. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
