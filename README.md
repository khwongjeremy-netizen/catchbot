# Catch — Discord bot

A Discord bot that keeps your group accountable with funny notifications,
goal tracking, and friend nudges — powered by your Catch Flask backend.

---

## Commands

| Command | What it does |
|---------|-------------|
| `/creategroup <name>` | Create a new Catch group |
| `/joingroup <invite_code>` | Join a group with an invite code |
| `/start <goal> <group_id>` | Set a goal and notify your group |
| `/done <goal_id>` | Mark your goal complete |
| `/nudge <@friend> <group_id>` | Send a funny nudge to a slacking friend |
| `/status <group_id>` | See who's working and who's slacking |

---

## Setup

### 1. Create a Discord bot

1. Go to **discord.com/developers/applications**
2. Click **New Application** → name it "Catch"
3. Go to **Bot** in the left sidebar → click **Add Bot**
4. Under **Privileged Gateway Intents**, turn on:
   - Server Members Intent
   - Message Content Intent
5. Click **Reset Token** → copy the token (you only see it once)
6. Go to **OAuth2 → URL Generator**:
   - Scopes: tick `bot` and `applications.commands`
   - Bot permissions: tick `Send Messages`, `Read Messages/View Channels`
   - Copy the generated URL → open it in your browser → invite the bot to your server

### 2. Install dependencies

```bash
cd catch-discord
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Open .env and paste your Discord bot token
```

### 4. Make sure your Flask backend is running

```bash
# In your catch-backend folder
source venv/bin/activate
python3 app.py
```

### 5. Run the bot

```bash
# In your catch-discord folder (new terminal tab)
source venv/bin/activate
python3 bot.py
```

You should see:
```
Catch bot online as Catch#1234
Synced 6 slash commands
```

---

## How it works

The bot connects to your existing Flask + Supabase backend.
When a user runs `/start`, the bot:
1. Sends the goal to your Flask API (`POST /goals/set`)
2. Posts a funny notification + gif to the Discord channel
3. When `/done` is called, checks if the whole group is finished
4. If everyone is done, sends a celebration message

Everything is stored in your Supabase database — the bot is just the notification layer on top.
