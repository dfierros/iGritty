"""
iGritty Databse Interface

"""

import datetime
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from typing import List, Optional, Union

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
from iGritty.common.utils import SupportedChannelType, SupportedTrainRecurrance

DB_LOCK_TIMEOUT_SECONDS: int = 10

logger = logging.getLogger("discord")


@dataclass
class iGrittyDB:
    db_name: str

    _conn: sqlite3.Connection = field(init=False, default=None)
    _cursor: sqlite3.Cursor = field(init=False, default=None)

    _db_lock: Lock = field(init=False, default=Lock())

    def __post_init__(self):
        sqlite3.register_adapter(datetime.date, adapt_date_iso)
        sqlite3.register_adapter(datetime.datetime, adapt_datetime_epoch)
        sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
        sqlite3.register_adapter(datetime.time, adapt_time_iso)
        sqlite3.register_converter("date", convert_date)
        sqlite3.register_converter("datetime", convert_datetime)
        sqlite3.register_converter("time", convert_time)
        sqlite3.register_converter("timestamp", convert_timestamp)

        with self._db_connect():
            logger.info("Initialized database: %s", self.db_name)

    @contextmanager
    def _db_connect(self, detect_types: bool = False):
        self._db_lock.acquire(DB_LOCK_TIMEOUT_SECONDS)
        try:
            self._conn = sqlite3.connect(
                self.db_name,
                detect_types=sqlite3.PARSE_DECLTYPES if detect_types else 0,
            )
            self._cursor = self.conn.cursor()
            logger.debug("Established database connection")
            yield
        finally:
            self._cursor = None
            self._conn.close()
            logger.debug("Closed database connection")
            self._db_lock.release()

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
            logger.debug("Setting up text channel table")
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
            logger.debug("Setting up voice channel table")
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
            logger.debug(
                "Add channels to table [%s %s %s]",
                channel_type,
                channel_id,
                channel_name,
            )
            self.cursor.execute(
                f"INSERT INTO {channel_type.value} (channel_id, channel_name) VALUES (?, ?)",
                (channel_id, channel_name),
            )
            self.conn.commit()

    def get_channels(self, channel_type: Union[str, SupportedChannelType]) -> List[tuple]:
        """
        Retrieve a list of all channels of the given type in the database

        Arguments:
            channel_type (str, SupportedChannelType): Channel type to add, normally 'voice' or 'text'

        Returns:
            List[tuple]: list of channel entries

        """
        channel_type = SupportedChannelType(channel_type)
        with self._db_connect():
            logger.debug("Get channels [%s]", channel_type)
            result = self.cursor.execute(f"SELECT id, channel_id, channel_name FROM {channel_type} ORDER BY id ASC")
            return result.fetchall()

    def get_id_for_channel(self, channel_type: Union[str, SupportedChannelType], channel_name: str) -> Optional[int]:
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
            logger.debug("Get ID for channel [%s, %s]", channel_type, channel_name)
            result = self.cursor.execute(
                f"SELECT * FROM {channel_type} WHERE channel_name like (?)",
                (channel_name,),
            )
            if output := result.fetchone():
                _, channel_id, _ = output
                return channel_id

        return None

    def setup_train_table(self):
        """
        Create a table to store information on game trains

        """
        with self._db_connect(detect_types=True):
            logger.debug("Setting up train table")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_game_trains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game TEXT,
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
        recurrance: Union[str, SupportedTrainRecurrance] = SupportedTrainRecurrance.ONCE,
    ):
        """
        Add a new train to the train table

        Arguments:
            game (str): Game for which the train should be run
            channel_name (str): channel on which the train should be run
            departure_time (datetime): departure time of the train
            recurrance (str, SupportedTrainRecurrance): how often the train should be run. Default Once

        Returns:
            (int): the most recently added row ID

        """
        recurrance = SupportedTrainRecurrance(recurrance)
        with self._db_connect(detect_types=True):
            logger.debug(
                "Adding train [%s, %s, %s, %s]",
                game,
                channel_name,
                departure_time,
                recurrance.value,
            )
            self.cursor.execute(
                "INSERT INTO scheduled_game_trains (game, channel_name, departure_datetime, recurrance)"
                " VALUES (?, ?, ?, ?)",
                (game, channel_name, departure_time, recurrance.value),
            )
            self.conn.commit()
            return self.cursor.lastrowid

    def get_trains(self, channel_name: Optional[str] = None) -> List[tuple]:
        """
        Retrieve a list of all scheduled trains

        Arguments:
            channel_name (str): channel for which to retrieve trains

        Returns:
            List[tuple]: list of train entries from the database in order of departure time

        """
        with self._db_connect(detect_types=True):
            logger.debug(
                "Getting trains%s",
                f"[ for channel {channel_name}]" if channel_name else "",
            )
            result = self.cursor.execute(
                "SELECT id, game, channel_name, departure_datetime, recurrance"
                " FROM scheduled_game_trains WHERE channel_name like (?)"
                " ORDER BY departure_datetime ASC",
                (channel_name if channel_name else "%",),
            )
            if output := result.fetchall():
                return output

        return []

    def remove_train(self, train_id: int):
        """
        Remove a train with given ID from the scheduled train table

        Arguments:
            train_id (int): unique identifier for the train to remove

        """
        if not isinstance(train_id, int):
            msg = "Provided train ID [%s] is not an integer, skipping removal" % train_id
            logger.error(msg)
            raise TypeError(msg)

        with self._db_connect(detect_types=True):
            result = self.cursor.execute(
                "SELECT id FROM scheduled_game_trains WHERE id = (?)",
                (train_id,),
            )
            if result.fetchone():
                logger.debug("Deleting train [id == %s]", train_id)
                self.cursor.execute(
                    "DELETE FROM scheduled_game_trains WHERE id = (?)",
                    (train_id,),
                )
                self.conn.commit()
            else:
                logger.error("Cannot delete nonexistant train [%s]", train_id)
                raise ValueError(f"No train with ID {train_id}")
