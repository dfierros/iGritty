"""
iGritty Bot Application

Notes:
    * This example requires the 'members' and 'message_content' privileged intents to function.

"""

import logging
import logging.handlers
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from iGritty import __version__ as bot_version
from iGritty.cogs.game_train_scheduler import GameTrainScheduler

# -------------
# Logging Setup
# -------------

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename="discord.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# ----------
# Bot Params
# ----------

load_dotenv()
API_KEY = os.getenv("BOT_TOKEN")
DESCRIPTION = "Gritty is trapped in a Discord Bot!"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    description=DESCRIPTION,
    intents=intents,
)

# ------------
# Bot Commands
# ------------


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")

    logger.info("Loading game train scheduler")
    await bot.add_cog(GameTrainScheduler(bot))
    logger.info("------")


@bot.command()
async def version(ctx: commands.Context):
    """
    Retrieve the bot version (visible only to you)

    """
    logger.info("Version requested")
    await ctx.send(f"iGritty Discord Bot version {bot_version}", ephemeral=True)


bot.run(API_KEY)
