"""
Background process to launch the game train

"""

import logging
from datetime import timedelta, timezone

import datetime
import discord
from discord.ext import commands, tasks
from zoneinfo import ZoneInfo

DEFAULT_TARGET_CHANNEL: int = 1348041444644094034

# If no tzinfo is given then UTC is assumed.
DEFAULT_LEAD_TIME_MINS: int = 10
TIMES = [
    datetime.time(hour=12, minute=50, tzinfo=timezone.utc),
]


logger = logging.getLogger("discord")


class GameTrainScheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.launch_scheduled_train.start()

    def cog_unload(self):
        self.launch_scheduled_train.cancel()

    async def _train(
        self,
        lead_time: timedelta = datetime.timedelta(minutes=DEFAULT_LEAD_TIME_MINS),
        poll_duration: timedelta = datetime.timedelta(hours=1),
        channel_id: int = DEFAULT_TARGET_CHANNEL,
    ):
        """
        Helper method which launches the train

        Arguments:
            lead_time (timedelta): how long from now the train should depart
            channel_id (int): channel at which the train departure should be announced

        """
        channel = self.bot.get_channel(channel_id)
        logger.info("Should send message to channel: %s", channel)

        train_poll = discord.Poll(
            question="You in?",
            duration=poll_duration,
        )
        train_poll.add_answer(text="Yea")
        train_poll.add_answer(text="Nah")

        departure_time = (
            datetime.datetime.now(tz=ZoneInfo("America/New_York")) - lead_time
        ).strftime("%I:%M %p")
        await channel.send(
            f"Game Train departing in {lead_time.seconds // 60} minutes! (At {departure_time} EST)",
            poll=train_poll,
        )

    @tasks.loop(time=TIMES)
    async def launch_scheduled_train(self):
        logger.info("Launching scheduled game train")
        await self._train()

    @commands.command(name="train")
    async def launch_train_now(
        self,
        ctx: commands.Context,
        lead_time_mins: int = DEFAULT_LEAD_TIME_MINS,
    ):
        """
        Launch the game train now in this channel

        """
        logger.info("Launching user-requested game train")
        await self._train(
            lead_time=timedelta(minutes=lead_time_mins),
            channel_id=ctx.channel.id,
        )
