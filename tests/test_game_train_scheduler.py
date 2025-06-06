"""
Unit tests for game_train_scheduler.py

"""

import pytest
import discord
from discord.ext import commands
import datetime
from iGritty.cogs.game_train_scheduler import GameTrainScheduler
from iGritty.db import iGrittyDB
from unittest.mock import AsyncMock


@pytest.fixture
def patch_discord(mocker, mock_poll):
    patched_discord = mocker.patch("iGritty.cogs.game_train_scheduler.discord")
    patched_discord.Poll.return_value = mock_poll
    return patched_discord


@pytest.fixture
def example_db(tmp_path) -> iGrittyDB:
    return iGrittyDB(tmp_path / "test.db")


@pytest.fixture
def mock_channel() -> discord.ChannelType:
    return AsyncMock()


@pytest.fixture
def mock_bot(mocker, mock_channel) -> commands.Bot:
    mock_bot = mocker.Mock(spec=commands.Bot)
    mock_bot.get_channel.return_value = mock_channel
    return mock_bot


@pytest.fixture
def mock_db(mocker) -> iGrittyDB:
    return mocker.Mock(spec=iGrittyDB)


@pytest.fixture
def mock_poll(mocker) -> discord.Poll:
    return mocker.Mock(spec=discord.Poll)


@pytest.fixture
def mock_train_scheduler(mocker, mock_bot, mock_db) -> GameTrainScheduler:
    mocker.patch.object(GameTrainScheduler, "_load_scheduled_trains")
    return GameTrainScheduler(mock_bot, mock_db)


class TestGameTrainScheduler:
    def test_construction(self, mocker):
        mock_load_scheduled_trains = mocker.patch.object(GameTrainScheduler, "_load_scheduled_trains")
        GameTrainScheduler(mocker.Mock(), mocker.Mock())
        mock_load_scheduled_trains.assert_called_once()

    def test_cog_unload(self, mocker, mock_train_scheduler):
        mock_scheduled_task_1 = mocker.Mock()
        mock_scheduled_task_2 = mocker.Mock()
        mock_train_scheduler._scheduled_train_tasks[1] = mock_scheduled_task_1
        mock_train_scheduler._scheduled_train_tasks[2] = mock_scheduled_task_2
        mock_train_scheduler.cog_unload()
        mock_scheduled_task_1.cancel.assert_called_once()
        mock_scheduled_task_2.cancel.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "channel_id, lead_time, add_poll, game_name, custom_message",
        [
            pytest.param(
                1,
                datetime.timedelta(minutes=10),
                False,
                None,
                None,
                id="DEFAULT_BEHAVIOR",
            ),
            pytest.param(
                1,
                datetime.timedelta(minutes=10),
                True,
                None,
                None,
                id="POLL_PROVIDED",
            ),
            pytest.param(
                1,
                datetime.timedelta(minutes=10),
                False,
                "Bad Rats",
                None,
                id="GAME_PROVIDED",
            ),
            pytest.param(
                1,
                datetime.timedelta(minutes=10),
                False,
                None,
                "Foo Bar",
                id="CUSTOM_MESSAGE_PROVIDED",
            ),
            pytest.param(
                1,
                datetime.timedelta(minutes=10),
                True,
                "Bad Rats",
                "Foo Bar",
                id="ALL_PARAMS_PROVIDED",
            ),
        ],
    )
    async def test_train(
        self,
        patch_discord,
        mock_poll,
        mock_train_scheduler,
        mock_channel,
        channel_id,
        lead_time,
        add_poll,
        game_name,
        custom_message,
    ):
        await mock_train_scheduler._train(channel_id, lead_time, add_poll, game_name, custom_message)

        if add_poll:
            patch_discord.Poll.assert_called_once_with(question="You in?", duration=datetime.timedelta(hours=1))
            mock_poll.add_answer.assert_called()
        else:
            patch_discord.Poll.assert_not_called()

        mock_channel.send.assert_awaited_once()
        print("Current time ==>", (datetime.datetime.now()).strftime("%I:%M %p"))
        print("Send message ==>", mock_channel.send.await_args[0])
