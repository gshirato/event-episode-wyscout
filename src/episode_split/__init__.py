from importlib.metadata import version

__version__ = version("episode_split")

from .episode.split import process

__all__ = [process]
