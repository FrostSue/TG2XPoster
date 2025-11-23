# TG2XPoster (Telegram to X/Twitter Auto Poster)

**TG2XPoster** is a professional, modular, and scalable automation tool designed to monitor a specific Telegram channel in real-time and mirror its content to a Twitter (X) account. It handles text, single photos, videos, and complex albums (grouped media) with zero latency using the Telegram Event API.

It features a robust **Role-Based Access Control (RBAC)** system, allowing secure management through **"Owner"** and **"Sudo"** roles directly from Telegram.

---

## 🚀 Key Features

* **⚡ Real-time Monitoring:** Uses Telegram's Event API for instant updates (no polling lag).
* **📸 Smart Media Handling:** Supports Photos, Videos, and **Albums (Grouped Media)**.
* **🧵 Auto-Threading:** Automatically splits long texts (>280 chars) into a Twitter thread without breaking words.
* **🛡️ Duplicate Prevention:** Tracks posted message IDs to prevent re-posting the same content.
* **🔐 Secure Access Control:** Features an **Owner & Sudo** system. Only authorized users can control the bot.
* **🐳 Docker Ready:** Fully containerized for easy deployment and scalability.
* **🔄 Resilient:** Includes automatic retry logic, rate-limit handling (HTTP 429), and auto-restart capabilities.
* **🛠️ Advanced Commands:** Check logs, status, or restart the system directly from Telegram.

---

## 📂 Project Structure

```text
TG2XPoster/
├── core/             # Configuration and Logging modules
├── telegram/         # Telegram logic
│   ├── listener.py   # Main event loop
│   └── commands.py   # Command handler & permission logic
├── twitter/          # Twitter API handlers
├── utils/            # Helper functions
│   ├── auth_manager.py # Owner/Sudo permission manager
│   ├── restarter.py    # System restart logic
│   └── notifier.py     # Telegram log notifier
├── data/             # Persistent storage (session, posted_ids, sudoers)
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
git clone https://github.com/FrostSue/TG2XPoster.git
cd TG2XPoster
```

### 2\. Configuration (.env)

Create a `.env` file in the root directory and fill in your credentials.
**CRITICAL:** Set your own Telegram ID as `ADMIN_USER_ID` to become the **Owner**.

```ini
# --- TELEGRAM SETTINGS ---
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=-100xxxxxxxxxx  # Channel to monitor

# --- SECURITY & LOGGING ---
TELEGRAM_LOG_CHANNEL_ID=-100xxxxxxxxxx # Channel for system logs
ADMIN_USER_ID=123456789  # <--- YOUR TELEGRAM ID (THE OWNER)

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

## 👑 Roles & Commands

The bot uses a strict permission system to prevent unauthorized access. Commands can be sent via Direct Message (DM) or in a group where the bot is present.

### 1\. Roles

  * **Owner:** Defined in `.env` (`ADMIN_USER_ID`). Has full access, including adding/removing admins.
  * **Sudo (Admin):** Added by the Owner. Can manage the bot (view logs, restart) but cannot add new admins.
  * **Public:** Can only view basic info (`/start`, `/help`).

### 2\. Command List

| Command | Description | Permission |
| :--- | :--- | :--- |
| **/start** | Bot introduction. | Public |
| **/help** | Shows available commands based on your role. | Public |
| **/status** | Displays uptime, tweet stats, and user role. | **Sudo + Owner** |
| **/ping** | Health check. Returns "Pong\!" if the bot is active. | **Sudo + Owner** |
| **/logs** | Fetches the last 15 lines of system logs. | **Sudo + Owner** |
| **/restart** | Reboots the bot process (Docker auto-restarts it). | **Sudo + Owner** |
| **/addsudo `<ID>`** | Grants admin privileges to a user ID. | **Owner Only** |
| **/rmsudo `<ID>`** | Revokes admin privileges from a user ID. | **Owner Only** |
| **/sudolist** | Lists all authorized Sudo admins. | **Owner Only** |

-----

## ⚠️ Important Notes

1.  **Telegram Permissions:** The bot must be an **Administrator** in the source Telegram channel to read messages effectively.
2.  **Twitter Permissions:** Ensure your Twitter App has **"Read and Write"** permissions enabled in the Developer Portal.
      * *Note: If you change permissions from Read-Only to Read/Write, you must regenerate your Access Token & Secret.*
3.  **Session Management:** The bot uses a persistent session file stored internally (in Docker) or in the `data/` directory to avoid re-login issues (Bad Salt errors) and ensure stability across restarts.
4.  **Security:** The `data/sudoers.json` file stores the list of authorized IDs locally. This file is persistent but excluded from Git to protect privacy.

-----

## 🤝 Contributing

Contributions, issues, and feature requests are welcome\! Feel free to check the [issues page](https://github.com/FrostSue/TG2XPoster/issues).

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
