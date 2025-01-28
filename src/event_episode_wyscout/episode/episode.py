from event_episode_wyscout.utils.episodes.data_row import get_episodes

from event_episode_wyscout.datasets.playerank import PlayerRank

from event_episode_wyscout.episode.base import EventEpisodes


class EventEpisodesWithSimpleFeatures(EventEpisodes):
    def __init__(self, events, match_info, player_info, team_info):
        self.events = events
        self.match_info = match_info
        self.player_info = player_info
        self.team_info = team_info

    def run(self):
        df = self.create_df()
        return df

    def create_df(self):
        res = get_episodes(self.events, self.match_info)
        res = self.rename_columns(res)

        # team_meta = get_team_meta(self.team_info)

        # # todo: move this to a separate function
        # res["naive.first_pass_team"] = res["naive.first_pass_team"].map(
        #     team_meta["name"].to_dict()
        # )
        # res["main_team"] = res["main_team"].map(team_meta["name"].to_dict())
        res = self.order_columns(res)
        return res

    def order_columns(self, df):
        return df[
            [
                "episode",
                "team_name",
                "event_name",
                "match_id",
                "match_period",
                "event_sec",
                "event_id",
                "sub_event_name",
                "sub_event_id",
                # "first_pass_team",
                "main_team",
                "tags",
                "id",
                "player_name",
                "team_id",
                "player_id",
                "start_x",
                "start_y",
                "end_x",
                "end_y",
                "incorrect_location",
                "change_of_possession",
                "change_of_possession.long_duration",
                "start_of_episode",
                "obvious.start_of_episode",
                "obvious.stop_event",
                "obvious._.prev_period",
                "obvious.half_start",
                "obvious.prev_stop_event",
                "obvious.set_piece_start",
                "obvious.long_pause",
                "obvious.episode",
                "naive.change_possession",
                "naive.change_of_team",
                "naive.episode",
                "naive.possession_duration",
                "naive.group_main",
                "naive.prev_group_main",
                "intermediate.episode",
                "intermediate.possession_duration",
                "intermediate.duration",
                "intermediate.prev_duration",
            ]
        ]

    def rename_columns(self, df):
        return df.rename(
            columns={
                "eventSec": "event_sec",
                "matchPeriod": "match_period",
                "eventName": "event_name",
                "subEventName": "sub_event_name",
                "teamId": "team_id",
                "matchId": "match_id",
                "eventId": "event_id",
                "subEventId": "sub_event_id",
                "playerId": "player_id",
            }
        )

    def assign_role(self, df, role_dict):
        def get_role(row):
            return role_dict.get((row["player_id"], row["match_id"]), "Unknown")

        df["role_simple"] = df.apply(get_role, axis=1)
        return df
