from importlib.metadata import version

__version__ = version("event-episode-wyscout")

from .episode.split import process

__all__ = [process]
