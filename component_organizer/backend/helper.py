import enum


class UnicodeEscape(enum.Enum):
    PLUS_MINUS = u"\u00B1"
    OHM = u"\u2126"

    def __str__(self):
        return self.value
