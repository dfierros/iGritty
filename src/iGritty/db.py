"""
iGritty Databse Interface

"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class iGrittyDB:
    db_name: str

    _conn: sqlite3.Connection = field(init=False, default=None)
    _cursor: sqlite3.Cursor = field(init=False, default=None)

    def __post_init__(self):
        self._conn = sqlite3.connect(self.db_name)
        self._cursor = self.conn.cursor()

    @contextmanager
    def _db_connect(self):
        try:
            self._conn = sqlite3.connect(self.db_name)
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
        # Create a table if it doesn't exist
        with self._db_connect:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS text_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    channel_name TEXT NOT NULL
                )
            """)
            self.conn.commit()

    def add_channel_to_table(self, channel_id: int, channel_name: str):
        with self._db_connect:
            self.cursor.execute(
                "INSERT INTO text_channels (channel_id, channel_name) VALUES (?, ?)",
                (channel_id, channel_name),
            )
            self.conn.commit()
