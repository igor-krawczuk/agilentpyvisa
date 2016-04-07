from enum import IntEnum
class Formats(IntEnum):
    default = 1


class Filter(IntEnum):
    disconnect = 0
    connect = 1


class Series(IntEnum):
    disconnect = 0
    connect = 1


class Range(IntEnum):
    default = 0


class Polarity(IntEnum):
    like_input = 0
    auto = 0
    manual = 1


