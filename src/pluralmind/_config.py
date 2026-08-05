from dataclasses import dataclass


@dataclass(slots=True)
class PluralmindConfig:
    cache_duration: int = 900
    """
    The amount of time to cache a system's data for, in seconds.
    After this time, the data will be considered expired and subsequent
    requests for it will result in a reload.

    Defaults to 15 minutes.
    """


config = PluralmindConfig()
