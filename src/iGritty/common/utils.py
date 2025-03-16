"""
Common utils

"""

from enum import Enum, auto


class StrEnum(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        """
        When using auto() on enum members will use the given name as the value

        """
        return name

    @classmethod
    def _missing_(cls, value):
        """
        If no enum member is found, try lowercase comparison if input is a string

        """
        if isinstance(value, str):
            for member in cls:
                if member.name.lower() == value.lower():
                    return member
        super()._missing_(value)


class SupportedChannelType(StrEnum):
    """Channel types supported for DB operations"""

    TEXT = "text_channels"
    VOICE = "voice_channels"


class SupportedTrainRecurrance(StrEnum):
    ONCE = auto()
    WEEKLY = auto()
    DAILY = auto()
