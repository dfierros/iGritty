"""
Background process to launch the game train

"""

import asyncio
import datetime
import logging
from datetime import timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from iGritty.common.params import DEBUG_MSG_DURATION_SECONDS
from iGritty.db import iGrittyDB

DEFAULT_LEAD_TIME_MINS: int = 10
TIMEZONE: ZoneInfo = ZoneInfo("America/New_York")

logger = logging.getLogger("discord")


class GameTrainScheduler(commands.Cog):
    """
    Game trains scheduler

    Arguments:
        bot (commands.Bot): discord bot interface
        db (iGrittyDB): database interface for saving trains to be restored upon bot reload

    """

    def __init__(
        self,
        bot: commands.Bot,
        db: iGrittyDB,
    ):
        self.bot = bot
        self.db = db
        self._scheduled_train_tasks = dict()
        logger.info("Loaded Game Train Schduler")
        self._load_scheduled_trains()

    def cog_unload(self):
        """
        When unloading this module...
        * Cancel any pending game trains

        """
        # Cancel any scheduled trains when unloaded
        for train_task in self._scheduled_train_tasks.values():
            logger.info("Cancelling %s", train_task)
            train_task.cancel()
        logger.info("Unloaded Game Train Schduler")

    def _load_scheduled_trains(self):
        """
        Load scheduled trains from the database, removing any that have expired

        """
        for train in self.db.get_trains():
            train_id, game, channel_name, departure_datetime, _ = train

            # If this train is expired, remove from the DB and skip to the next train
            if departure_datetime < datetime.datetime.now():
                logger.warning("Removing expired scheduled train [%s]", train)
                self.db.remove_train(train_id)
                continue
            else:
                logger.info("Loading scheduled train [%s]", train)

            channel_id = self.db.get_id_for_channel("text", channel_name=channel_name)

            task = asyncio.create_task(
                self.run_train_at_time(
                    game=game, start_time=departure_datetime, channel_id=channel_id
                )
            )
            self._scheduled_train_tasks[train_id] = task
            # Have this train remove itself from the scheduled train map upon completion
            task.add_done_callback(lambda _: self._scheduled_train_tasks.pop(train_id))

    async def _train(
        self,
        channel_id: int,
        game_name: Optional[str] = None,
        lead_time: timedelta = datetime.timedelta(minutes=DEFAULT_LEAD_TIME_MINS),
        poll_duration: timedelta = datetime.timedelta(hours=1),
    ):
        """
        Helper method which launches the train

        Arguments:
            channel_id (int): channel at which the train departure should be announced
            game_name (str, optional): the name of the game for the train
            lead_time (timedelta): how long from now the train should depart
            poll_duration (timedelta): how long the train poll should run

        """
        channel = self.bot.get_channel(channel_id)
        logger.info("Should send message to channel: %s", channel)

        train_poll = discord.Poll(
            question="You in?",
            duration=poll_duration,
        )
        train_poll.add_answer(text="Yea")
        train_poll.add_answer(text="Nah")

        departure_time = (datetime.datetime.now(tz=TIMEZONE) - lead_time).strftime(
            "%I:%M %p"
        )

        msg = f"Game Train departing in {lead_time.seconds // 60} minutes! (At {departure_time} EST)"
        if game_name:
            msg = f"[{game_name}] {msg}"
        await channel.send(msg, poll=train_poll)

    async def wait_until(self, time: datetime.datetime):
        """
        Task which waits for a given time

        Arguments:
            time (datetime.datetime): time for which to wait

        """
        now = datetime.datetime.now()
        await asyncio.sleep((time - now).total_seconds())

    async def run_train_at_time(
        self, game: str, start_time: datetime.datetime, channel_id: int
    ):
        """
        Run a train at some time in the future

        Arguments:
            game (str): game for which the train should run
            start_time (datetime.datetime): time at which the train should depart
            channel_id (int): channel on which the train should run

        """
        if start_time < datetime.datetime.now():
            logger.error("Cannot schedule past train at %s", start_time)
        else:
            await self.wait_until(start_time)
            await self._train(channel_id=channel_id, game_name=game)
            logger.info("Scheduled train complete")

    # --------------------
    # User-facing commands
    # --------------------

    @commands.command(name="schedule_train")
    async def schedule_train(
        self,
        ctx: commands.Context,
        time_str: str,
        game: Optional[str] = None,
        date_str: Optional[str] = None,
        channel_id: Optional[int] = None,
    ):
        """
        Schedule a game train for departure at a specific time

        Arguments:
            ctx (commands.Context): context in which this command is called
            time_str (str): The time to run the train, HH:MM format, must still be today
            game (str, optional): game for which to schedule the train
            date_str (str, optional): The date to run the train, DD/MM/YYYY format, must be in the future.
                If not provided, assume today
            channel_id (int, optional): the channel in which to launch the train.
                If not provided, assume the channel in which the command is called

        """
        logger.info(
            "Scheduled game train requested [%s]",
            (game, time_str, date_str, channel_id),
        )

        # Get the date
        if date_str is None:
            date = datetime.datetime.now()
        else:
            date = datetime.datetime.strptime(date_str, "%d/%m/%Y")

        run_time = datetime.datetime.strptime(time_str, "%H:%M").replace(
            year=date.year, month=date.month, day=date.day
        )

        # Ensure that this train is scheduled for the future
        now = datetime.datetime.now()
        delay = (run_time - now).total_seconds()
        if delay < 0:
            msg = f"Cannot schedule train for the past ({run_time.strftime('%Y-%m-%d %H:%M:%S')})"
            await ctx.send(msg, delete_after=DEBUG_MSG_DURATION_SECONDS)
            logger.error(msg)

        # Get the channel
        if channel_id is not None:
            channel = self.bot.get_channel(int(channel_id))
        else:
            channel = ctx.channel

        if channel is None:
            msg = "Unable to determine channel to run train"
            await ctx.send(msg, delete_after=DEBUG_MSG_DURATION_SECONDS)
            logger.error(msg)

        task = asyncio.create_task(
            self.run_train_at_time(
                game=game, start_time=run_time, channel_id=channel.id
            )
        )

        train_id = self.db.add_train_to_table(game, channel.name, run_time)
        self._scheduled_train_tasks[train_id] = task
        self.db.add_channel_to_table("text", channel.id, channel.name)

        logger.info(
            "Scheduled a game train at %s in channel %s for game: %s",
            run_time.strftime("%Y-%m-%d %H:%M:%S"),
            channel,
            game,
        )
        await ctx.channel.send(
            f"All set, game train will depart in {delay / 60:.2f} minutes,"
            f" at {run_time.strftime('%Y-%m-%d %H:%M:%S')}!"
        )

    @commands.command(name="upcoming_trains")
    async def upcoming_trains(
        self,
        ctx: commands.Context,
        channel_id: Optional[int] = None,
    ):
        """
        List the upcoming trains

        Arguments:
            ctx (commands.Context): context in which this command is called
            channel_id (int, optional): the channel for which to check for trains

        """
        logger.info("Upcoming trains requested [%s]", channel_id)

        # If channel is provided, only list upcoming trains in the given channel
        channel = None
        if channel_id is not None:
            channel = self.bot.get_channel(int(channel_id))

        if upcoming_trains := self.db.get_trains(
            channel_name=channel.name if channel else None
        ):
            msg = [f"The next [{len(upcoming_trains)}] train(s) are: "]
            for train in upcoming_trains:
                train_id, game, channel_name, departure_datetime, _ = train
                msg.append(
                    f"* Train #{train_id} in {channel_name} departing at {departure_datetime}"
                    f"{f' for {game}' if game else ''}"
                )
            await ctx.channel.send(
                "\n".join(msg), delete_after=DEBUG_MSG_DURATION_SECONDS
            )
        else:
            await ctx.channel.send("No upcoming trains!")

    @commands.command(name="cancel_train")
    async def cancel_train(self, ctx: commands.Context, train_id: int):
        """
        Cancel the given train

        Arguments:
            ctx (commands.Context): context in which this command is called
            train_id (int): the train which should be cancelled

        """
        logger.info("Train cancellation requested [%s]", train_id)

        if train_task := self._scheduled_train_tasks.get(train_id):
            train_task.cancel()
            self.db.remove_train(train_id)
            await ctx.channel.send(
                f"Removed train #{train_id} from the schedule",
            )
        else:
            await ctx.channel.send(
                f"No train with id {train_id} found",
                delete_after=DEBUG_MSG_DURATION_SECONDS,
            )

    @commands.command(name="train")
    async def launch_train_now(self, ctx: commands.Context, game: Optional[str] = None):
        """
        Launch the game train now in this channel

        Arguments:
            ctx (commands.Context): context in which this command is called
            game (str, optional): game for which to run the train

        """
        logger.info("Launching user-requested game train for game %s", game)
        await self._train(channel_id=ctx.channel.id, game_name=game)
