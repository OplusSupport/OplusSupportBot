# O+ SUPPORT — OplusSupportBot

A production-ready Telegram support bot for **OPPO, OnePlus & Realme** unlocking
services (FRP, Flash, Auth), built with **Python 3.12** and
**python-telegram-bot v21+**. Designed to run 24/7 on **Render.com**.

- **Bot name:** O+ SUPPORT
- **Owner:** [@the_hitman_show](https://t.me/the_hitman_show)
- **Website:** https://www.opluspro.net

---

## ✨ Features

- Full command set: `/start`, `/help`, `/status`, `/frp`, `/flash`, `/auth`,
  `/price`, `/contact`, `/website`, `/support`, `/ping`
- Keyword auto-reply — anyone typing `status`, `frp`, `flash`, `auth`,
  `price`, `website`, `support`, `contact`, `hello`, or `hi` gets an
  instant reply, no `/` needed
- Beautiful inline keyboards for menu navigation
- Markdown-formatted messages
- Welcome message for new group members
- Automatic deletion of Telegram invite links posted by non-admins
- Basic anti-spam (rate limiting) with auto-mute
- Admin-only moderation commands: `/ban`, `/unban`, `/mute`, `/unmute`, `/warn`
- Structured logging
- Long-polling — no webhook/SSL setup required, works out of the box on Render

---

## 📁 Project Structure

```
OplusSupportBot/
│
├── main.py           # Bot logic, handlers, moderation, admin commands
├── config.py          # Environment-variable based configuration
├── messages.py        # All bot text/message templates
├── requirements.txt    # Python dependencies
├── Procfile            # Process definition (worker)
├── render.yaml          # Render.com deploy blueprint
├── runtime.txt           # Pinned Python version
├── README.md              # You're reading it
└── .gitignore
```

---

## 🔑 Environment Variables

| Variable                | Required | Default            | Description                                             |
|-------------------------|:--------:|---------------------|-----------------------------------------------------------|
| `BOT_TOKEN`              | ✅ Yes   | —                    | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS`               | No       | *(empty)*            | Comma-separated numeric Telegram user IDs treated as bot admins everywhere, e.g. `123456789,987654321` |
| `BOT_NAME`                | No       | `O+ SUPPORT`          | Display name used inside messages |
| `OWNER_USERNAME`           | No       | `@the_hitman_show`    | Telegram contact shown in `/contact` |
| `WEBSITE_URL`               | No       | `https://www.opluspro.net` | Website shown in `/website` and `/contact` |
| `MAX_WARNINGS`               | No       | `3`                  | Warnings before `/warn` auto-bans a user |
| `ANTI_SPAM_MSG_LIMIT`         | No       | `6`                  | Max messages allowed within the time window |
| `ANTI_SPAM_TIME_WINDOW`        | No       | `8`                  | Sliding window (seconds) used for spam detection |
| `ANTI_SPAM_MUTE_SECONDS`         | No       | `300`                 | Mute duration (seconds) applied to detected spammers |
| `DELETE_INVITE_LINKS`             | No       | `true`                | Set `false` to disable invite-link deletion |
| `ENABLE_WELCOME_MESSAGE`            | No       | `true`                | Set `false` to disable welcome messages |
| `ENABLE_ANTI_SPAM`                   | No       | `true`                | Set `false` to disable anti-spam muting |
| `LOG_LEVEL`                            | No       | `INFO`                | Python logging level |

⚠️ **Never commit your `BOT_TOKEN` to GitHub.** It is only ever read from the
environment via `os.getenv("BOT_TOKEN")` in `config.py` — it is never
hardcoded anywhere in this project.

---

## 🚀 Getting a Bot Token

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts (choose a name and a username
   ending in `bot`, e.g. `OplusSupportBot`).
3. BotFather will reply with a token that looks like:
   `123456789:AAExampleTokenStringGoesHere`
4. Keep this token secret — you'll paste it into Render as `BOT_TOKEN`
   in the steps below.

To make yourself a bot admin (so `/ban`, `/mute`, etc. work for you even
outside a group), get your numeric Telegram user ID from
[@userinfobot](https://t.me/userinfobot) and set it as `ADMIN_IDS`.

---

## 🐙 1. Upload the Project to GitHub

```bash
# From inside the OplusSupportBot/ folder:
git init
git add .
git commit -m "Initial commit - OplusSupportBot"

# Create a new repository on github.com first, then:
git branch -M main
git remote add origin https://github.com/<your-username>/OplusSupportBot.git
git push -u origin main
```

> Make sure `.gitignore` is committed so your local `.env` (if you create
> one for local testing) never gets pushed to GitHub.

---

## ☁️ 2. Deploy to Render.com

### Option A — One-click via `render.yaml` (recommended)

1. Log in to [Render.com](https://render.com) and click **New +** →
   **Blueprint**.
2. Connect your GitHub account and select the `OplusSupportBot` repository.
3. Render will detect `render.yaml` automatically and show the
   `oplus-support-bot` **Worker** service to create.
4. Click **Apply**. Render will ask you to fill in the environment
   variables marked `sync: false` (`BOT_TOKEN`, `ADMIN_IDS`) — enter your
   real bot token there.
5. Click **Create** / **Deploy**. Render will build and start the worker
   automatically.

### Option B — Manual setup

1. Log in to [Render.com](https://render.com) and click **New +** →
   **Background Worker**.
2. Connect the `OplusSupportBot` GitHub repository.
3. Configure:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
4. Under **Environment Variables**, add at minimum:
   - `BOT_TOKEN` = *your token from BotFather*
   - `ADMIN_IDS` = *your numeric Telegram user ID(s), comma-separated*
5. Click **Create Background Worker**. Render will build and deploy.

> A **Background Worker** service type is used (not a Web Service) because
> this bot uses long-polling and doesn't need to accept inbound HTTP
> requests or bind to a port. Render keeps worker services running 24/7.

---

## 🖥️ 3. Run Locally (optional, for testing)

```bash
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt

export BOT_TOKEN="your-token-here"     # on Windows (PowerShell): $env:BOT_TOKEN="your-token-here"
export ADMIN_IDS="123456789"

python main.py
```

---

## 🛡 Admin Commands (group chats only)

Reply to the target user's message with one of the following. Usable by
Telegram group admins/owner, or any ID listed in `ADMIN_IDS`:

| Command    | Effect                                  |
|------------|------------------------------------------|
| `/ban`      | Bans the replied-to user from the group    |
| `/unban`     | Unbans the replied-to user                  |
| `/mute`       | Restricts the replied-to user from sending messages |
| `/unmute`      | Restores normal sending permissions           |
| `/warn`         | Adds a warning; auto-bans at `MAX_WARNINGS`     |

Make sure the bot itself has **Delete Messages**, **Ban Users**, and
**Restrict Members** admin permissions inside your Telegram group,
otherwise these actions will fail.

---

## 🧩 Notes on Persistence

Warnings and anti-spam counters are kept **in memory** for simplicity —
they reset if the process restarts. For high-traffic groups needing
permanent history, swap the in-memory dictionaries in `main.py`
(`user_warnings`, `spam_tracker`) for a database (e.g. Redis or
PostgreSQL).

---

## 📄 License

This project is provided as-is for O+ SUPPORT / opluspro.net.
