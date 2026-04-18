import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import random
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
FLASK_API     = os.getenv("FLASK_API", "http://localhost:5000")

# ── Bot setup ─────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ── Reaction pools ────────────────────────────────────────────
ACTIVE_GIFS = [
    "https://media.giphy.com/media/LmNwrBhejkK9EFP504/giphy.gif",  # person typing fast
    "https://media.giphy.com/media/13GIgrGdslD9oQ/giphy.gif",      # working hard
    "https://media.giphy.com/media/xT9IgzoKnwFNmISR8I/giphy.gif",  # lets go
]
ACTIVE_EMOJIS  = ["💪", "🔥", "⚡", "🚀", "😤", "👀"]

COMPLETE_GIFS = [
    "https://media.giphy.com/media/3oz8xAFtqoOUUrsh7W/giphy.gif",  # celebration
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",   # party
    "https://media.giphy.com/media/artj92V8o75VPL7AeQ/giphy.gif",  # well done
]
COMPLETE_EMOJIS = ["🎉", "✅", "🏆", "🙌", "🎊", "👏"]

NUDGE_GIFS = [
    "https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif",  # sleeping
    "https://media.giphy.com/media/xT9IgG6DSjflDyOuAg/giphy.gif",  # phone addict
    "https://media.giphy.com/media/l2JehQ2GitHGdVG9y/giphy.gif",   # lazy
]
NUDGE_EMOJIS = ["😴", "📱", "🦥", "🐌", "👀", "⏰"]

ALL_DONE_GIFS = [
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/3oz8xAFtqoOUUrsh7W/giphy.gif",
]

# ── Active messages when someone starts working ───────────────
ACTIVE_MESSAGES = [
    "{name} just started working on **{goal}** {emoji} — are you still on your phone?",
    "{emoji} heads up — {name} is grinding on **{goal}** while you're not",
    "{name} locked in on **{goal}** {emoji} don't let them get ahead of you",
    "🚨 {name} is being productive right now. **{goal}** is getting done. what's your excuse?",
    "{emoji} {name} said let's get it — working on **{goal}** rn",
]

# ── Messages when someone completes a goal ────────────────────
COMPLETE_MESSAGES = [
    "{emoji} {name} just finished **{goal}** — respect 👏",
    "{name} COMPLETED **{goal}** {emoji} — are you done yet?",
    "✅ {name} checked off **{goal}** {emoji} one step closer to that meal",
    "{emoji} {name} is done with **{goal}** — the group reward is getting closer...",
    "{name} finished **{goal}** {emoji} — catch up!",
]

# ── Message when the whole group finishes ─────────────────────
ALL_DONE_MESSAGES = [
    "🎉 EVERYONE IS DONE! Time to go catch up over food — you all earned it",
    "🏆 The whole squad finished their goals! Go celebrate — you deserve it",
    "🍕 ALL GOALS COMPLETE! Group dinner time — let's catch up",
]


# ── Helper: call Flask API ─────────────────────────────────────
async def api_post(endpoint: str, data: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{FLASK_API}{endpoint}", json=data) as r:
            return await r.json(), r.status

async def api_get(endpoint: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{FLASK_API}{endpoint}") as r:
            return await r.json(), r.status


# ── Bot ready ──────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"Catch bot online as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Sync error: {e}")
    check_nudges.start()


# ── /start command ─────────────────────────────────────────────
# User sets a goal — notifies everyone else in the channel
@tree.command(name="start", description="Set a goal and go active — your group gets notified")
@app_commands.describe(goal="What are you working on?", group_id="Your Catch group ID")
async def start(interaction: discord.Interaction, goal: str, group_id: str):
    user_id = f"discord_{interaction.user.id}"
    data, status = await api_post("/goals/set", {
        "user_id":     user_id,
        "group_id":    group_id,
        "description": goal,
    })

    if status != 201:
        await interaction.response.send_message(
            f"❌ Couldn't set goal: {data.get('error', 'unknown error')}",
            ephemeral=True
        )
        return

    goal_id = data["goal"]["id"]
    emoji   = random.choice(ACTIVE_EMOJIS)
    gif     = random.choice(ACTIVE_GIFS)
    msg     = random.choice(ACTIVE_MESSAGES).format(
        name=interaction.user.display_name, goal=goal, emoji=emoji
    )

    # Confirm to the user privately
    await interaction.response.send_message(
        f"✅ Goal set! Your group is being notified...\n**Goal ID:** `{goal_id}` *(save this to mark done later)*",
        ephemeral=True
    )

    # Broadcast to the channel
    await interaction.channel.send(f"{msg}\n{gif}")


# ── /done command ──────────────────────────────────────────────
# User marks a goal complete — notifies everyone, checks if group is all done
@tree.command(name="done", description="Mark your goal as complete")
@app_commands.describe(goal_id="The goal ID you got when you ran /start")
async def done(interaction: discord.Interaction, goal_id: str):
    user_id = f"discord_{interaction.user.id}"
    data, status = await api_post(f"/goals/{goal_id}/complete", {
        "user_id": user_id
    })

    if status != 200:
        await interaction.response.send_message(
            f"❌ Couldn't complete goal: {data.get('error', 'unknown error')}",
            ephemeral=True
        )
        return

    emoji = random.choice(COMPLETE_EMOJIS)
    gif   = random.choice(COMPLETE_GIFS)
    msg   = random.choice(COMPLETE_MESSAGES).format(
        name=interaction.user.display_name,
        goal=data["goal"]["description"],
        emoji=emoji
    )

    await interaction.response.send_message(
        "✅ Marked as done — your group is being notified!", ephemeral=True
    )

    # Broadcast completion
    await interaction.channel.send(f"{msg}\n{gif}")

    # If everyone in the group is done, send the celebration message
    if data.get("group_all_done"):
        all_done_msg = random.choice(ALL_DONE_MESSAGES)
        gif2 = random.choice(ALL_DONE_GIFS)
        await interaction.channel.send(f"\n{all_done_msg}\n{gif2}")


# ── /nudge command ─────────────────────────────────────────────
# Manually nudge a friend by @mentioning them
@tree.command(name="nudge", description="Nudge a friend who's slacking")
@app_commands.describe(
    friend="@ the friend you want to nudge",
    group_id="Your Catch group ID",
    caption="Optional roast message"
)
async def nudge(
    interaction: discord.Interaction,
    friend: discord.Member,
    group_id: str,
    caption: str = ""
):
    from_id = f"discord_{interaction.user.id}"
    to_id   = f"discord_{friend.id}"
    emoji   = random.choice(NUDGE_EMOJIS)
    gif     = random.choice(NUDGE_GIFS)

    # Save nudge to backend
    await api_post("/nudges/send", {
        "from_user_id": from_id,
        "to_user_id":   to_id,
        "group_id":     group_id,
        "image_url":    emoji,
        "caption":      caption or "get off your phone and work!",
    })

    roast = caption if caption else "get off your phone and work!"
    msg = (
        f"{emoji} {friend.mention} — **{interaction.user.display_name}** is already working\n"
        f"*\"{roast}\"*\n{gif}"
    )

    await interaction.response.send_message(msg)


# ── /creategroup command ───────────────────────────────────────
@tree.command(name="creategroup", description="Create a new Catch group")
@app_commands.describe(name="Name for your group")
async def creategroup(interaction: discord.Interaction, name: str):
    user_id = f"discord_{interaction.user.id}"
    data, status = await api_post("/groups/create", {
        "name":       name,
        "created_by": user_id,
    })

    if status != 201:
        await interaction.response.send_message(
            f"❌ {data.get('error', 'Could not create group')}",
            ephemeral=True
        )
        return

    group    = data["group"]
    inv_code = data["invite_code"]
    await interaction.response.send_message(
        f"✅ Group **{name}** created!\n"
        f"**Group ID:** `{group['id']}`\n"
        f"**Invite code:** `{inv_code}`\n\n"
        f"Share the invite code with your friends so they can join with `/joingroup`",
        ephemeral=True
    )


# ── /joingroup command ─────────────────────────────────────────
@tree.command(name="joingroup", description="Join a Catch group with an invite code")
@app_commands.describe(invite_code="The invite code from your friend")
async def joingroup(interaction: discord.Interaction, invite_code: str):
    user_id = f"discord_{interaction.user.id}"
    data, status = await api_post("/groups/join", {
        "invite_code": invite_code,
        "user_id":     user_id,
    })

    if status == 404:
        await interaction.response.send_message("❌ Invalid invite code — double check it", ephemeral=True)
        return
    if status not in (200, 201):
        await interaction.response.send_message(f"❌ {data.get('error', 'Could not join')}", ephemeral=True)
        return

    group = data["group"]
    await interaction.response.send_message(
        f"✅ Joined **{group['name']}**!\n"
        f"**Group ID:** `{group['id']}`\n\n"
        f"Use `/start` with this group ID when you begin working",
        ephemeral=True
    )


# ── /status command ────────────────────────────────────────────
# Shows who's active and who's slacking in a group
@tree.command(name="status", description="See who's working and who's slacking in your group")
@app_commands.describe(group_id="Your Catch group ID")
async def status(interaction: discord.Interaction, group_id: str):
    data, status_code = await api_get(f"/goals/group/{group_id}")

    if status_code != 200:
        await interaction.response.send_message("❌ Couldn't load group status", ephemeral=True)
        return

    goals = data.get("goals", [])
    if not goals:
        await interaction.response.send_message("No goals set in this group yet — use `/start` to begin!", ephemeral=True)
        return

    active = [g for g in goals if g["status"] == "active"]
    done   = [g for g in goals if g["status"] == "done"]

    lines = ["**Catch group status**\n"]
    if active:
        lines.append("🔥 **Working:**")
        for g in active:
            lines.append(f"  • `{g['user_id'].replace('discord_','')}` — {g['description']}")
    if done:
        lines.append("\n✅ **Done:**")
        for g in done:
            lines.append(f"  • ~~{g['description']}~~")
    if not active and not done:
        lines.append("Nobody has started yet — use `/start` to kick things off!")

    await interaction.response.send_message("\n".join(lines))


# ── Background task: auto-nudge anyone who hasn't started ──────
# Runs every 60 minutes and sends a nudge to channels where
# some members are active but others haven't set a goal
@tasks.loop(minutes=60)
async def check_nudges():
    # This is a placeholder — in production you'd store
    # which Discord channel belongs to which group and
    # cross-reference active vs inactive members
    pass


# ── Run ────────────────────────────────────────────────────────
bot.run(DISCORD_TOKEN)
