import pandas as pd
from wyscout_api import APIHandler
from data_container.datasets.event.hudl.fromData import EventFromData
from episode_split.segment.segment import segment_events

from episode_split.helper import get_inter_start_ids
from episode_split.episode.characterize import add_episode_info


def get_df_with_episode(handler: APIHandler, match_id: int) -> pd.DataFrame:
    _event = handler.retrieve_event_data(match_id)["events"]
    event = EventFromData(pd.DataFrame(_event), fps=25)

    start_events, end_events, loose_ball, gk_exit_splits = segment_events(_event)

    res = event.get_data()

    res["loose_ball"] = res["id"].isin(loose_ball)
    res["loose_start"] = res["loose_ball"] & (
        res["loose_ball"].shift(1) != res["loose_ball"]
    )
    res["loose_end"] = res["loose_ball"] & (
        res["loose_ball"].shift(-1) != res["loose_ball"]
    )

    res["clear_start"] = res["id"].isin(start_events)
    res["clear_end"] = res["id"].isin(end_events)
    res["clear_start"] = res["clear_start"] | res["clear_end"].shift(1).fillna(True)

    res["clear_episode"] = res["clear_start"].cumsum()

    res["next.location.x.pct"] = res["location.x.pct"].shift(-1)
    res["next.location.y.pct"] = res["location.y.pct"].shift(-1)
    res["next.team.name"] = res["team.name"].shift(-1)

    inter_start_ids = (
        res.groupby("clear_episode")
        .apply(get_inter_start_ids)
        .set_index("id")["inter.start"]
        .keys()
    )
    res["inter.start"] = res["id"].isin(inter_start_ids)

    res["before_loose_end"] = res["loose_end"].shift(-1).fillna(False)
    res["after_loose_end"] = res["loose_end"].shift(1).fillna(False)
    res["gk_exit_split"] = res["id"].isin(gk_exit_splits)

    res["start"] = (
        res["clear_start"]
        | res["inter.start"]
        | res["after_loose_end"]
        | res["gk_exit_split"]
    )

    res["episode"] = res["start"].cumsum()
    return res


def process(
    handler: APIHandler,
    match_id: int,
) -> pd.DataFrame:
    df = get_df_with_episode(handler, match_id)
    df = add_episode_info(df)
    return df
