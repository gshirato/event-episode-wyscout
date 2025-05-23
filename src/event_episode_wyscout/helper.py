import pandas as pd
from data_container.datasets.event.hudl.fromData import EventFromData
from event_episode_wyscout.segment.segment import segment_events





def get_intermediate_start(df_episode):
    df_episode = df_episode.copy()
    start = df_episode.iloc[0]
    df_episode["small.first"] = df_episode["id"] == start["id"]
    df_episode["long_enough"] = (df_episode["small.episode.count"] > 1) & (
        df_episode["small.episode.duration"] > 3
    )

    duration_map = df_episode.drop_duplicates("small.episode")[
        ["small.episode", "small.episode.duration"]
    ].set_index("small.episode")["small.episode.duration"]

    df_episode["prev.small.episode.duration"] = df_episode["small.episode"].map(
        lambda x: duration_map.get(x - 1, None)
    )

    inter_start = (
        ~df_episode["small.first"]
        & df_episode["long_enough"]
        & df_episode["prev.small.episode.duration"].gt(3)
        & df_episode["change.team"]
        & ~df_episode["loose_ball"]
    )
    return inter_start


def get_inter_start_ids(df):
    res = df[df["type.secondary"].map(lambda x: "defensive_duel" not in x)]
    res["change.team"] = res["team.name"].shift(1) != res["team.name"]
    res["small.episode"] = res["change.team"].cumsum()
    duration = res.groupby("small.episode")["video.duration"].sum().to_dict()
    count = res.groupby("small.episode")["id"].count().to_dict()
    res["small.episode.duration"] = res["small.episode"].map(duration)
    res["small.episode.count"] = res["small.episode"].map(count)

    res["inter.start"] = get_intermediate_start(res)
    return res[res["inter.start"]]


def get_df_with_episode(handler, match_id):
    _event = handler.retrieve_event_data(match_id)["events"]
    event = EventFromData(pd.DataFrame(_event), fps=25)

    start_events, end_events, loose_ball = segment_events(_event)

    res = event.get_data()

    res["loose_ball"] = res["id"].isin(loose_ball)
    res["loose_start"] = res["loose_ball"] & (
        res["loose_ball"].shift(1) != res["loose_ball"]
    )
    res["loose_end"] = res["loose_ball"] & (
        res["loose_ball"].shift(-1) != res["loose_ball"]
    )

    res["clear_start"] = res["id"].isin(start_events)
    res["clear_end"] = res["id"].isin(end_events) | res["loose_end"]
    res["clear_start"] = (
        res["clear_start"] | res["clear_end"].shift(1).fillna(True)
        # | df["loose_start"]
    )

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

    res["start"] = res["clear_start"] | res["inter.start"]

    res["episode"] = res["start"].cumsum()
    return res
