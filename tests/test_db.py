"""
Unit tests for db.py

"""

import datetime

import pytest

from iGritty.db import iGrittyDB


@pytest.fixture
def example_db(tmp_path) -> iGrittyDB:
    return iGrittyDB(tmp_path / "test.db")


class TestiGrittyDB:
    def test_channel_table(self, example_db):
        example_db.setup_text_channel_table()
        example_db.setup_voice_channel_table()

        example_db.add_channel_to_table("voice", 1, "channel_1")
        example_db.add_channel_to_table("voice", 2, "channel_2")
        example_db.add_channel_to_table("text", 1, "channel_one")
        example_db.add_channel_to_table("text", 2, "channel_two")

        assert example_db.get_channels("voice") == [
            (1, 1, "channel_1"),
            (2, 2, "channel_2"),
        ]
        assert example_db.get_channels("text") == [
            (1, 1, "channel_one"),
            (2, 2, "channel_two"),
        ]

        assert example_db.get_id_for_channel("voice", "channel_2") == 2
        assert not example_db.get_id_for_channel("voice", "NONEXISTANT")

        assert example_db.get_id_for_channel("text", "channel_one") == 1
        assert not example_db.get_id_for_channel("text", "NONEXISTANT")

    def test_train_table(self, example_db):
        example_db.setup_train_table()

        right_now = datetime.datetime.now()
        in_an_hour = right_now + datetime.timedelta(hours=1)
        tomorrow = right_now + datetime.timedelta(days=1)
        yesterday = right_now - datetime.timedelta(days=1)

        example_db.add_train_to_table(
            "Bad Rats",
            "cool_channel",
            in_an_hour,
        )

        # assert example_db.get_trains() == [
        #     (1, "Bad Rats", "cool_channel", "2025-03-15T14:47:41.339052", "ONCE"),
        # ]

        example_db.add_train_to_table(
            "Half Life 3",
            "other_channel",
            tomorrow,
            "DAILY",
        )

        # assert example_db.get_trains() == [
        #     (1, "Bad Rats", "cool_channel", "2025-03-15T14:47:41.339052", "ONCE"),
        #     (2, "Half Life 3", "other_channel", "2025-03-16T13:47:41.339052", "DAILY"),
        # ]

        example_db.add_train_to_table(
            "Dota 1",
            "no channel",
            yesterday,
            "WEEKLY",
        )

        assert example_db.get_trains() == [
            (3, "Dota 1", "no channel", yesterday.timestamp(), "WEEKLY"),
            (1, "Bad Rats", "cool_channel", in_an_hour.timestamp(), "ONCE"),
            (2, "Half Life 3", "other_channel", tomorrow.timestamp(), "DAILY"),
        ]
