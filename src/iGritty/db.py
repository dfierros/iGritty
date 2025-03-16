"""
iGritty Databse Interface

"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
import datetime
from typing import Union, Optional, List

from iGritty.common.db_utils import (
    adapt_date_iso,
    adapt_datetime_epoch,
    adapt_datetime_iso,
    adapt_time_iso,
    convert_date,
    convert_datetime,
    convert_time,
    convert_timestamp,
)
from iGritty.common.utils import StrEnum
from enum import auto


class SupportedChannelType(StrEnum):
    """Channel types supported for DB operations"""

    TEXT = "text_channels"
    VOICE = "voice_channels"


class SupportedTrainRecurrance(StrEnum):
    ONCE = auto()
    WEEKLY = auto()
    DAILY = auto()


@dataclass
class iGrittyDB:
    db_name: str

    _conn: sqlite3.Connection = field(init=False, default=None)
    _cursor: sqlite3.Cursor = field(init=False, default=None)

    def __post_init__(self):
        sqlite3.register_adapter(datetime.date, adapt_date_iso)
        sqlite3.register_adapter(datetime.datetime, adapt_datetime_epoch)
        sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
        sqlite3.register_adapter(datetime.time, adapt_time_iso)
        sqlite3.register_converter("date", convert_date)
        sqlite3.register_converter("datetime", convert_datetime)
        sqlite3.register_converter("time", convert_time)
        sqlite3.register_converter("timestamp", convert_timestamp)

        self._conn = sqlite3.connect(self.db_name)
        self._cursor = self.conn.cursor()

    @contextmanager
    def _db_connect(self, detect_types: bool = False):
        try:
            self._conn = sqlite3.connect(
                self.db_name,
                detect_types=sqlite3.PARSE_DECLTYPES if detect_types else 0,
            )
            self._cursor = self.conn.cursor()
            yield
        finally:
            self._cursor = None
            self._conn.close()

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    @property
    def cursor(self) -> sqlite3.Cursor:
        return self._cursor

    def setup_text_channel_table(self):
        """
        Create a table to store text channel information, or do nothing if the table already exists

        """
        with self._db_connect():
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {SupportedChannelType.TEXT.value} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    channel_name TEXT NOT NULL
                )
            """)
            self.conn.commit()

    def setup_voice_channel_table(self):
        """
        Create a table to store voice channel information, or do nothing if the table already exists

        """
        with self._db_connect():
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {SupportedChannelType.VOICE.value} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    channel_name TEXT NOT NULL
                )
            """)
            self.conn.commit()

    def add_channel_to_table(
        self,
        channel_type: Union[str, SupportedChannelType],
        channel_id: int,
        channel_name: str,
    ):
        """
        Add a new channel to the channel table

        Arguments:
            channel_type (str, SupportedChannelType): Channel type to add, normally 'voice' or 'text'
            channel_id (int): unique channel identifier
            channel_name (str): potentially not unique channel name

        """
        channel_type = SupportedChannelType(channel_type)
        with self._db_connect():
            self.cursor.execute(
                f"INSERT INTO {channel_type.value} (channel_id, channel_name) VALUES (?, ?)",
                (channel_id, channel_name),
            )
            self.conn.commit()

    def get_channels(
        self, channel_type: Union[str, SupportedChannelType]
    ) -> List[tuple]:
        """
        Retrieve a list of all channels of the given type in the database

        Arguments:
            channel_type (str, SupportedChannelType): Channel type to add, normally 'voice' or 'text'

        Returns:
            List[tuple]: list of channel entries

        """
        channel_type = SupportedChannelType(channel_type)
        with self._db_connect():
            result = self.cursor.execute(
                f"SELECT id, channel_id, channel_name FROM {channel_type} ORDER BY id ASC"
            )
            return result.fetchall()

    def get_id_for_channel(
        self, channel_type: Union[str, SupportedChannelType], channel_name: str
    ) -> Optional[int]:
        """
        Retrieve an ID which maps to the given channel name

        Arguments:
            channel_type (str, SupportedChannelType): Channel type to add, normally 'voice' or 'text'
            channel_name (str): channel name for which an ID should be found

        Returns:
            Optional[int]: channel ID if the given channel was found, othwerise None

        """
        channel_type = SupportedChannelType(channel_type)
        with self._db_connect():
            result = self.cursor.execute(
                f"SELECT * FROM {channel_type} WHERE channel_name like (?)",
                (channel_name,),
            )
            if output := result.fetchone():
                _, channel_id, _ = output
                return channel_id

    def setup_train_table(self):
        """
        Create a table to store information on game trains

        """
        with self._db_connect(detect_types=True):
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_game_trains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    departure_datetime datetime NOT NULL,
                    recurrance TEXT NOT NULL
                )
            """)
            self.conn.commit()

    def add_train_to_table(
        self,
        game: str,
        channel_name: str,
        departure_time: datetime,
        recurrance: Union[
            str, SupportedTrainRecurrance
        ] = SupportedTrainRecurrance.ONCE,
    ):
        """
        Add a new train to the train table

        Arguments:
            game (str): Game for which the train should be run

        """
        recurrance = SupportedTrainRecurrance(recurrance)
        with self._db_connect():
            self.cursor.execute(
                "INSERT INTO scheduled_game_trains (game, channel_name, departure_datetime, recurrance)"
                " VALUES (?, ?, ?, ?)",
                (game, channel_name, departure_time, recurrance.value),
            )
            self.conn.commit()

    def get_trains(self, channel_name: Optional[str] = None) -> List[tuple]:
        with self._db_connect():
            result = self.cursor.execute(
                "SELECT * FROM scheduled_game_trains WHERE channel_name like (?)"
                " ORDER BY departure_datetime ASC",
                (channel_name if channel_name else "%"),
            )
            if output := result.fetchall():
                return output
