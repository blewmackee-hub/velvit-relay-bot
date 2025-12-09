import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
RELAY_CHANNEL_ID = int(os.getenv("RELAY_CHANNEL_ID"))
OWNER_NAME = os.getenv("OWNER_NAME", "Velvit")

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


def format_user(user: discord.User | discord.Member) -> str:
    return f"{user.name} ({user.id})"


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Relay bot is running.")

    relay_channel = bot.get_channel(RELAY_CHANNEL_ID)
    if relay_channel is None:
        print("WARNING: Relay channel not found. Check RELAY_CHANNEL_ID.")
    else:
        await relay_channel.send(f"✅ {OWNER_NAME}'s relay bot is now online.")


@bot.event
async def on_message(message: discord.Message):
    # Ignore self
    if message.author.bot:
        return

    # 1️⃣ DMs from users → forward to relay channel
    if isinstance(message.channel, discord.DMChannel):
        relay_channel = bot.get_channel(RELAY_CHANNEL_ID)
        if relay_channel is None:
            print("Relay channel not found.")
            return

        embed = discord.Embed(
            title="New DM to Relay",
            description=message.content or "*no text*",
            color=discord.Color.blue(),
        )
        embed.add_field(name="From", value=format_user(message.author), inline=False)

        if message.attachments:
            files_text = "\n".join(a.url for a in message.attachments)
            embed.add_field(name="Attachments", value=files_text, inline=False)

        await relay_channel.send(embed=embed)

        # Acknowledge in DM
        await message.channel.send(
            f"Hi! Your message has been relayed to **{OWNER_NAME}**. "
            "They'll see it soon 💌"
        )

    # 2️⃣ Messages in relay channel starting with !reply → send DM back
    elif message.channel.id == RELAY_CHANNEL_ID and message.content.startswith("!reply"):
        parts = message.content.split(maxsplit=2)

        if len(parts) < 3:
            await message.channel.send(
                "Usage: `!reply <user_id> <your message>`\n"
                "Example: `!reply 123456789012345678 Hey, I got your DM!`"
            )
            return

        user_id_str, reply_text = parts[1], parts[2]

        try:
            user_id = int(user_id_str)
        except ValueError:
            await message.channel.send("❌ Invalid user ID.")
            return

        user = bot.get_user(user_id)
        if user is None:
            try:
                user = await bot.fetch_user(user_id)
            except Exception as e:
                await message.channel.send(f"❌ Could not fetch user: {e}")
                return

        try:
            await user.send(f"📨 Message from **{OWNER_NAME}**:\n{reply_text}")
            await message.channel.send(f"✅ Sent reply to {format_user(user)}")
        except discord.Forbidden:
            await message.channel.send("❌ I can't DM that user (they may have DMs disabled).")

    # Allow commands to work
    await bot.process_commands(message)


@bot.command(name="contact")
async def contact(ctx: commands.Context):
    """Tell users how to DM the bot."""
    await ctx.send(
        "To contact "
        f"**{OWNER_NAME}**, just DM me directly and I'll relay your message 💬"
    )


bot.run(TOKEN)
