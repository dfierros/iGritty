"""
Unit tests for game_train_scheduler.py

"""

import pytest

from iGritty.db import iGrittyDB
from iGritty.cogs.game_train_scheduler import GameTrainScheduler


@pytest.fixture
def example_db(tmp_path) -> iGrittyDB:
    return iGrittyDB(tmp_path / "test.db")


@pytest.fixture
def mock_train_scheduler(mocker) -> GameTrainScheduler:
    mocker.patch.object(GameTrainScheduler, "_load_scheduled_trains")
    return GameTrainScheduler(mocker.Mock(), mocker.Mock())


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
