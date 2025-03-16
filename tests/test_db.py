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

        assert example_db.get_trains() == []

        # First, try adding 3 items to the DB and reading them back
        assert (
            example_db.add_train_to_table(
                "Bad Rats",
                "cool_channel",
                in_an_hour,
            )
            == 1
        )

        assert example_db.get_trains() == [
            (1, "Bad Rats", "cool_channel", in_an_hour, "ONCE"),
        ]

        assert (
            example_db.add_train_to_table(
                "Half Life 3",
                "other_channel",
                tomorrow,
                "DAILY",
            )
            == 2
        )

        assert example_db.get_trains() == [
            (1, "Bad Rats", "cool_channel", in_an_hour, "ONCE"),
            (2, "Half Life 3", "other_channel", tomorrow, "DAILY"),
        ]

        assert (
            example_db.add_train_to_table(
                "Dota 1",
                "no channel",
                yesterday,
                "WEEKLY",
            )
            == 3
        )

        assert example_db.get_trains() == [
            (3, "Dota 1", "no channel", yesterday, "WEEKLY"),
            (1, "Bad Rats", "cool_channel", in_an_hour, "ONCE"),
            (2, "Half Life 3", "other_channel", tomorrow, "DAILY"),
        ]

        # Then, try removing 2 items from the DB
        example_db.remove_train(1)

        assert example_db.get_trains() == [
            (3, "Dota 1", "no channel", yesterday, "WEEKLY"),
            (2, "Half Life 3", "other_channel", tomorrow, "DAILY"),
        ]

        example_db.remove_train(3)

        assert example_db.get_trains() == [
            (2, "Half Life 3", "other_channel", tomorrow, "DAILY"),
        ]

        # Finally, try removing adding back 1 item to the DB
        assert (
            example_db.add_train_to_table("Hairspray", "pool_channel", tomorrow, "ONCE")
            == 4
        )

        assert example_db.get_trains() == [
            (2, "Half Life 3", "other_channel", tomorrow, "DAILY"),
            (4, "Hairspray", "pool_channel", tomorrow, "ONCE"),
        ]

        # Invalid input testing
        with pytest.raises(TypeError):
            example_db.remove_train("string_input")

        with pytest.raises(ValueError):
            example_db.remove_train(123)
