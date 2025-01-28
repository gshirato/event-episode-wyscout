from abc import ABC, abstractmethod


class EventEpisodes(ABC):
    @abstractmethod
    def create_df(self):
        pass

    @abstractmethod
    def run_and_save_df(self):
        pass
