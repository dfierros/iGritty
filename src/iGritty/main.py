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
from iGritty.common.params import DEBUG_MSG_DURATION_SECONDS
from iGritty.db import iGrittyDB

# -------------
# Logging Setup
# -------------

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename="logs/discord.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")
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
    command_prefix="!",
    description=DESCRIPTION,
    intents=intents,
)

# ------------
# Bot Commands
# ------------


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")

    db = iGrittyDB("database/bot.db")
    db.setup_text_channel_table()
    db.setup_train_table()
    await bot.add_cog(GameTrainScheduler(bot, db))
    logger.info("------")


@bot.command()
async def version(ctx: commands.Context):
    """
    Retrieve the bot version (message is removed after 10 seconds)

    """
    logger.info("Version requested [%s]", bot_version)
    await ctx.send(
        f"iGritty Discord Bot version {bot_version}",
        delete_after=DEBUG_MSG_DURATION_SECONDS,
    )


bot.run(API_KEY)
