"""
config.py
----------
Central configuration for OplusSupportBot.

All sensitive values (like the bot token) are read from environment
variables. NEVER hardcode secrets in this file.
"""

import os


def _get_int_list_from_env(var_name: str) -> list:
    """Parse a comma-separated list of integers from an environment variable."""
    raw = os.getenv(var_name, "")
    result = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit() or (part.startswith("-") and part[1:].isdigit()):
            result.append(int(part))
    return result


# ---------------------------------------------------------------------------
# Core bot credentials / identity
# ---------------------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # REQUIRED - set this in Render environment variables

BOT_NAME = os.getenv("BOT_NAME", "O+ SUPPORT")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@the_hitman_show")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://www.opluspro.net")

# ---------------------------------------------------------------------------
# Admin configuration
# ---------------------------------------------------------------------------
# Comma-separated Telegram numeric user IDs that are treated as bot-level
# admins regardless of their status in a particular group.
# Example in Render env vars: ADMIN_IDS=123456789,987654321
ADMIN_IDS = _get_int_list_from_env("ADMIN_IDS")

# ---------------------------------------------------------------------------
# Anti-spam configuration
# ---------------------------------------------------------------------------
ANTI_SPAM_MSG_LIMIT = int(os.getenv("ANTI_SPAM_MSG_LIMIT", "6"))       # max messages
ANTI_SPAM_TIME_WINDOW = int(os.getenv("ANTI_SPAM_TIME_WINDOW", "8"))   # seconds
ANTI_SPAM_MUTE_SECONDS = int(os.getenv("ANTI_SPAM_MUTE_SECONDS", "300"))  # 5 min mute

# ---------------------------------------------------------------------------
# Warning system
# ---------------------------------------------------------------------------
MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", "3"))

# ---------------------------------------------------------------------------
# Feature toggles
# ---------------------------------------------------------------------------
DELETE_INVITE_LINKS = os.getenv("DELETE_INVITE_LINKS", "true").lower() == "true"
ENABLE_WELCOME_MESSAGE = os.getenv("ENABLE_WELCOME_MESSAGE", "true").lower() == "true"
ENABLE_ANTI_SPAM = os.getenv("ENABLE_ANTI_SPAM", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
