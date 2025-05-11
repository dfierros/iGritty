"""
Background process to launch the game train

"""

import asyncio
import datetime
import logging
from datetime import timedelta
from typing import Callable, Optional, Union
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from iGritty.common.utils import SupportedTrainRecurrance
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

    def _train_completion_callback_factory(self, train_id: int, reucrrance: SupportedTrainRecurrance) -> Callable:
        """
        Create a callback function to be executed when a train is launched

        Arguments:
            train_id (int): the train which has just run
            recurrance (SupportedTrainRecurrance): the recurrance rule for this train

        Returns:
            Callable: function which should be called by closing coroutine

        """

        def _train_completion_callback(train_task: asyncio.Future):
            """
            Upon execution:
            * Remove this train ID from the scheduled_train_tasks map
            * If this train does not recur, remove from database

            """
            self._scheduled_train_tasks.pop(train_id)
            if reucrrance == SupportedTrainRecurrance.ONCE:
                self.db.remove_train(train_id)

        return _train_completion_callback

    def _load_scheduled_trains(self):
        """
        Load scheduled trains from the database, removing any that have expired

        """
        for train in self.db.get_trains():
            train_id, game, channel_name, departure_datetime, recurrance = train
            now = datetime.datetime.now()

            # If this train is expired...
            if departure_datetime < now:
                # ...and no recurrance, remove this train
                if recurrance == SupportedTrainRecurrance.ONCE:
                    logger.warning("Removing expired scheduled train [%s]", train)
                    self.db.remove_train(train_id)
                # ...and has recurrance, simply skip adding the task
                else:
                    logger.info("Skipping train which is past for today [%s]", train)

                continue
            # If this train has a daily recurrance, adjust the time to run today
            elif recurrance == SupportedTrainRecurrance.DAILY:
                logger.info("Updating daily scheduled train to run today [%s]", train)
                departure_datetime.replace(year=now.year, month=now.month, day=now.day)
            else:
                logger.info("Loading scheduled train [%s]", train)

            channel_id = self.db.get_id_for_channel("text", channel_name=channel_name)

            task = asyncio.create_task(
                self.run_train_at_time(game=game, start_time=departure_datetime, channel_id=channel_id)
            )
            self._scheduled_train_tasks[train_id] = task

            # Have this train remove itself from the scheduled train map upon completion
            task.add_done_callback(self._train_completion_callback_factory(train_id, recurrance))

    async def _train(
        self,
        channel_id: int,
        lead_time: timedelta = datetime.timedelta(minutes=DEFAULT_LEAD_TIME_MINS),
        add_poll: bool = False,
        game_name: Optional[str] = None,
        custom_message: Optional[str] = None,
    ):
        """
        Helper method which launches the train

        Arguments:
            channel_id (int): channel at which the train departure should be announced
            lead_time (timedelta): how long from now the train should depart
            add_poll (bool): whether to include a poll with the train, default False
            game_name (str, optional): the name of the game for the train
            custom_message (str, optional): whether to use a custom train message, default auto-generated
        """
        channel = self.bot.get_channel(channel_id)
        logger.info("Should send %s train to channel: %s", channel)

        departure_time = (datetime.datetime.now(tz=TIMEZONE) + lead_time).strftime("%I:%M %p")

        if custom_message:
            msg = custom_message
        else:
            msg = f"Game Train departing in {lead_time.seconds // 60} minutes! (At {departure_time} EST)"

        if game_name:
            msg = f"[{game_name}] {msg}"

        if add_poll:
            train_poll = discord.Poll(
                question="You in?",
                duration=datetime.timedelta(hours=1),  # Polls have a minimum duration of 1 hour
            )
            train_poll.add_answer(text="Yea")
            train_poll.add_answer(text="Nah")

        await channel.send(msg, poll=train_poll if add_poll else None)

    async def wait_until(self, time: datetime.datetime):
        """
        Task which waits for a given time

        Arguments:
            time (datetime.datetime): time for which to wait

        """
        now = datetime.datetime.now()
        await asyncio.sleep((time - now).total_seconds())

    async def run_train_at_time(self, game: str, start_time: datetime.datetime, channel_id: int):
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
        recurrance: Union[str, SupportedTrainRecurrance] = SupportedTrainRecurrance.ONCE,
        date_str: Optional[str] = None,
        channel_id: Optional[int] = None,
    ):
        """
        Schedule a game train for departure at a specific time

        Arguments:
            ctx (commands.Context): context in which this command is called
            time_str (str): The time to run the train, HH:MM format, must still be today
            game (str, optional): game for which to schedule the train
            recurrance (str, optional): game for which to schedule the train
            date_str (str, optional): The date to run the train, DD/MM/YYYY format, must be in the future.
                If not provided, assume today
            channel_id (int, optional): the channel in which to launch the train.
                If not provided, assume the channel in which the command is called

        """
        recurrance = SupportedTrainRecurrance(recurrance)
        logger.info(
            "Scheduled game train requested [%s]",
            (time_str, game, recurrance, date_str, channel_id),
        )

        # Get the date
        if date_str is None:
            date = datetime.datetime.now()
        else:
            date = datetime.datetime.strptime(date_str, "%d/%m/%Y")

        run_time = datetime.datetime.strptime(time_str, "%H:%M").replace(year=date.year, month=date.month, day=date.day)

        # Ensure that this train is scheduled for the future
        now = datetime.datetime.now()
        delay = (run_time - now).total_seconds()
        if delay < 0:
            msg = f"Cannot schedule train for the past ({run_time.strftime('%Y-%m-%d %H:%M:%S')})"
            await ctx.send(msg)
            logger.error(msg)

        # Get the channel
        if channel_id is not None:
            channel = self.bot.get_channel(int(channel_id))
        else:
            channel = ctx.channel

        if channel is None:
            msg = "Unable to determine channel to run train"
            await ctx.send(msg)
            logger.error(msg)

        task = asyncio.create_task(self.run_train_at_time(game=game, start_time=run_time, channel_id=channel.id))

        train_id = self.db.add_train_to_table(game, channel.name, run_time, recurrance)
        self._scheduled_train_tasks[train_id] = task
        self.db.add_channel_to_table("text", channel.id, channel.name)

        logger.info(
            "Scheduled a game train at %s in channel %s for game %s, recurrance %s",
            run_time.strftime("%Y-%m-%d %H:%M:%S"),
            channel,
            game,
            recurrance,
        )

        msg = (
            f"All set, game train will depart in {delay / 60:.2f} minutes, at {run_time.strftime('%Y-%m-%d %H:%M:%S')}!"
        )
        if recurrance != SupportedTrainRecurrance.ONCE:
            msg += f" (will repeat {recurrance.value.lower()})"

        await ctx.channel.send(msg)

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

        if upcoming_trains := self.db.get_trains(channel_name=channel.name if channel else None):
            msg = [f"The next [{len(upcoming_trains)}] train(s) are: "]
            for train in upcoming_trains:
                train_id, game, channel_name, departure_datetime, _ = train
                msg.append(
                    f"* Train #{train_id} in {channel_name} departing at {departure_datetime}"
                    f"{f' for {game}' if game else ''}"
                )
            await ctx.channel.send("\n".join(msg))
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
            await ctx.channel.send(f"No train with id {train_id} found")

    @commands.command(name="train")
    async def launch_train_now(
        self,
        ctx: commands.Context,
        game: Optional[str] = None,
        custom_message: Optional[str] = None,
        add_poll: bool = False,
    ):
        """
        Launch the game train now in this channel

        Arguments:
            ctx (commands.Context): context in which this command is called
            game (str, optional): game for which to run the train

        """
        logger.info("Launching user-requested game train for game %s", game)
        await self._train(
            channel_id=ctx.channel.id,
            game_name=game,
            custom_message=custom_message,
            add_poll=add_poll,
        )
