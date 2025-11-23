# TG2XPoster (Telegram to X/Twitter Auto Poster)

**TG2XPoster** is a professional, modular, and scalable automation tool designed to monitor a specific Telegram channel in real-time and mirror its content to a Twitter (X) account. It handles text, single photos, videos, and complex albums (grouped media) with zero latency using the Telegram Event API.

-----

## 🚀 Key Features

* **⚡ Real-time Monitoring:** Uses Telegram's Event API for instant updates (no polling lag).
* **📸 Smart Media Handling:** Supports Photos, Videos, and **Albums (Grouped Media)**.
* **🧵 Auto-Threading:** Automatically splits long texts (>280 chars) into a Twitter thread without breaking words.
* **🛡️ Duplicate Prevention:** Tracks posted message IDs to prevent re-posting the same content.
* **🐳 Docker Ready:** Fully containerized for easy deployment and scalability.
* **🔄 Resilient:** Includes automatic retry logic and rate-limit handling (HTTP 429).
* **👥 Group Admin Control:** Manage the bot from any Telegram group by adding it as an admin.
* **🛠️ Advanced Commands:** Check logs, status, or restart the system directly from Telegram.

-----

## 📂 Project Structure

```text
TG2XPoster/
├── core/             # Configuration and Logging modules
├── telegram/         # Listener, command router & permission checks
│   ├── listener.py
│   └── commands.py   # Command logic (/start, /help, /status, etc.)
├── twitter/          # Twitter API v2 & v1.1 handlers
├── utils/            # Helper functions (formatting, storage, notifier, restarter)
├── data/             # Persistent storage (auth session & posted_ids)
├── .env              # API Keys (Not included in repo)
├── docker-compose.yml
├── Dockerfile
├── main.py           # Entry point
└── requirements.txt
````

-----

## 🛠️ Installation & Setup

### Prerequisites

  * Python 3.9+ OR Docker
  * Telegram API Credentials (`api_id`, `api_hash`)
  * Telegram Bot Token
  * Twitter (X) Developer Account (API Key & Access Tokens with **Read & Write** permissions)

### 1\. Clone the Repository

```bash
git clone [https://github.com/FrostSue/TG2XPoster.git](https://github.com/FrostSue/TG2XPoster.git)
cd TG2XPoster
```

### 2\. Configuration (.env)

Create a `.env` file in the root directory and fill in your credentials:

```ini
# --- TELEGRAM SETTINGS ---
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=-100xxxxxxxxxx  # Channel to monitor

# --- LOGGING ---
TELEGRAM_LOG_CHANNEL_ID=-100xxxxxxxxxx 
# --- TWITTER (X) SETTINGS ---
TWITTER_API_KEY=your_consumer_key
TWITTER_API_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# --- SYSTEM ---
LOG_LEVEL=INFO
```

-----

## 🚀 Usage

### Option A: Running with Docker (Recommended)

The easiest way to run the bot is using Docker Compose. This ensures the environment is isolated and runs restart policies automatically.

```bash
# Build and start the container
docker-compose up -d --build

# View logs to check status
docker-compose logs -f
```

### Option B: Running Manually (Python)

If you prefer running it directly on your machine:

1.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Bot:**

    ```bash
    python main.py
    ```

-----

## 🎮 Bot Commands

To control the bot, **add the bot to a Telegram group** and promote it to an administrator. Any administrator in that group can then use these commands.

| Command | Description | Permission |
| :--- | :--- | :--- |
| **/start** | Displays introduction and basic info about the bot. | Public |
| **/help** | Shows the list of available commands. | Public |
| **/status** | Displays system uptime, total tweets sent, and monitoring details. | **Admin Only** |
| **/logs** | Fetches and displays the last 15 lines of the system log file. | **Admin Only** |
| **/ping** | Simple health check. Returns "Pong\!" if the bot is active. | **Admin Only** |
| **/restart** | Restarts the bot process (Docker will auto-reload it). | **Admin Only** |

-----

## ⚠️ Important Notes

1.  **Telegram Permissions:** The bot must be an **Administrator** in the source Telegram channel to read messages effectively.
2.  **Twitter Permissions:** Ensure your Twitter App has **"Read and Write"** permissions enabled in the Developer Portal.
      * *Note: If you change permissions from Read-Only to Read/Write, you must regenerate your Access Token & Secret.*
3.  **Session Management:** The bot uses a persistent session file stored in the `data/` directory to avoid re-login issues (Bad Salt errors) and ensure stability across restarts.
4.  **Group Management:** Commands are designed to work in groups. Private messages (DM) may not support admin privilege checks correctly.

-----

## 🤝 Contributing

Contributions, issues, and feature requests are welcome\! Feel free to check the [issues page](https://github.com/FrostSue/TG2XPoster/issues).

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.