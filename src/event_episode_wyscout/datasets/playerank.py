import pandas as pd


class PlayerRank:

    def __init__(self, conf):
        self.conf = conf
        self.df = self.get_df()

    def get_df(self):
        return pd.read_json(self.conf["player_rank"])

    def role_dict(self):
        return self.df.set_index(["playerId", "matchId"])["roleCluster"].to_dict()

    def score_dict(self):
        return self.df.set_index(["playerId", "matchId"])["playerankScore"].to_dict()
