import numpy as np
import pandas as pd

from event_episode_wyscout.episode.FootballEventFilter import FootballEventFilter
from event_episode_wyscout.utils.coordinates import (
    get_coordinates_in_meters,
    calculate_distance,
)


def preprocess(events):
    res = pd.json_normalize(events)
    res["eventSec"] = res["videoTimestamp"].astype(float).map(lambda x: round(x, 3))

    res["start_x"] = res["location.x"]
    res["start_y"] = res["location.y"]
    res["end_x"] = res[["pass.endLocation.x", "carry.endLocation.x"]].apply(
        lambda x: x[0] if x[0] is not None else x[1] if x[1] is not None else None,
        axis=1,
    )
    res["end_y"] = res[["pass.endLocation.y", "carry.endLocation.y"]].apply(
        lambda x: x[0] if x[0] is not None else x[1] if x[1] is not None else None,
        axis=1,
    )

    res = get_flags(res)
    return res


def get_flags(df):
    """
    Get flags for
    - whether the location is incorrect
    - whether the action is accurate
    """
    res = df.copy()
    res = incorrect_location_flags(res)
    res = accurate_flags(res)
    return res


def accurate_flags(df):
    res = df.copy()
    res["accurate"] = res["pass.accurate"]
    return res


def incorrect_location_flags(df):
    return df


def flip_location(df, xmax, ymax):
    """
    We do not consider xmin and ymin now.
    """

    def flip(row, colname, vmax):
        if row["flipped"]:
            return vmax - row[colname]
        return row[colname]

    res = df.copy()
    res["start_x"] = res.apply(flip, colname="start_x", vmax=xmax, axis=1)
    res["start_y"] = res.apply(flip, colname="start_y", vmax=ymax, axis=1)
    res["end_x"] = res.apply(flip, colname="end_x", vmax=xmax, axis=1)
    res["end_y"] = res.apply(flip, colname="end_y", vmax=ymax, axis=1)
    return res


def get_flipped(df):
    def is_flipped(x, first_pass_team):
        return x["teamId"] != first_pass_team[(x["matchId"], x["obvious.episode"])]

    res = df.copy()
    # problem is that the calculation is done before the episode is determined
    # and the algorithms are mixed

    first_pass_team_by_group = (
        res.groupby(["matchId", "obvious.episode"])
        .apply(find_first_team_in_naive_episode)
        .to_dict()
    )
    res["naive.first_pass_team"] = res.apply(
        lambda row: first_pass_team_by_group[(row["matchId"], row["obvious.episode"])],
        axis=1,
    )
    res["flipped"] = res.apply(
        is_flipped, first_pass_team=first_pass_team_by_group, axis=1
    )
    return res


def get_stop_event(df, stop_events):
    res = df.copy()
    res["obvious._.next_event"] = res["type.primary"].shift(-1)
    non_saved = res.apply(lambda x: x["obvious._.next_event"] != "Save attempt", axis=1)
    is_stop_events = res.apply(lambda x: x["type.primary"] in stop_events, axis=1)
    res["obvious.stop_event"] = is_stop_events & non_saved

    return res


def get_long_pause(df, threshold):
    res = df.copy()
    prev_sec = res["eventSec"].shift(1)
    res["obvious.long_pause"] = res["eventSec"] - prev_sec > threshold
    return res


def process_groups(df, stop_events):
    res = df.copy()

    res = get_stop_event(res, stop_events)

    res["obvious._.prev_period"] = res["matchPeriod"].shift(1)
    res["obvious.half_start"] = res.apply(
        lambda x: x["matchPeriod"] != x["obvious._.prev_period"], axis=1
    )
    res["obvious.set_piece_start"] = res.apply(
        lambda x: x["type.primary"] == "Free Kick", axis=1
    )
    res["obvious.prev_stop_event"] = res["obvious.stop_event"].shift(1)
    res = get_long_pause(res, 30)
    res["obvious.start_of_episode"] = res.apply(
        lambda x: x["obvious.half_start"]
        or x["obvious.set_piece_start"]
        or x["obvious.long_pause"]
        or x["obvious.prev_stop_event"],
        axis=1,
    )

    res["obvious.episode"] = res["obvious.start_of_episode"].cumsum()
    return res


def split_into_episodes(
    match_events,
    stop_events=(
        "shot",
        "fairplay",
        "infraction",
        "game_interruption",
        "offside",
        "shot_against",
        "goalkeeper_exit",
    ),
):
    res = preprocess(match_events.data)
    res = process_groups(res, stop_events)
    res = get_flipped(res)
    res = flip_location(res, xmax=100, ymax=100)
    res = res.groupby("matchId", as_index=False).apply(adjust_episodes)
    res = get_main_team(res)
    res = get_coordinates_in_meters(res)
    res = calculate_distance(res)
    return res.reset_index(drop=True)


def get_main_team(df):
    res = df.copy()
    res["main_team"] = res.groupby("episode")["teamId"].transform(
        lambda x: x.value_counts().idxmax()
    )
    return res


def get_naive_episodes(df):
    res = df.copy()
    res["naive.change_of_team"] = res["teamId"] != res["teamId"].shift(1)
    res["naive.change_possession"] = res["naive.first_pass_team"] != res[
        "naive.first_pass_team"
    ].shift(1)
    res["naive.episode"] = (
        res["naive.change_of_team"]
        | res["naive.change_possession"]
        | res["obvious.start_of_episode"]
    ).cumsum()

    return res


def group_main_in_naive_episode(df, main_team):
    res = df.copy()
    res["naive.group_main"] = res["naive.episode"].map(main_team.to_dict())
    res["naive.group_main"] = res.apply(lambda x: adjust_main_team(x), axis=1).ffill()
    return res


def adjust_main_team(row):
    if row["naive.possession_duration"] < 5:
        return None
    return row["naive.group_main"]


def add_change_of_possession(df):
    res = df.copy()
    res = res.reset_index(drop=True)
    first_team = res.groupby("naive.episode").apply(find_majority_team_in_episode)
    res = group_main_in_naive_episode(res, first_team)
    res["naive.prev_group_main"] = res["naive.group_main"].shift(1)

    res["intermediate.episode"] = (
        res["naive.group_main"] != res["naive.prev_group_main"]
    ).cumsum()

    res["intermediate.possession_duration"] = get_duration(res, "intermediate.episode")

    duration = res.groupby("intermediate.episode")[
        "intermediate.possession_duration"
    ].median()
    # what's the difference from intermediate.possession_duration?
    res["intermediate.duration"] = res["intermediate.episode"].map(duration.to_dict())

    prev_duration = duration.shift(1)
    res["intermediate.prev_duration"] = res["intermediate.episode"].map(
        prev_duration.to_dict()
    )

    res["change_of_possession"] = res.apply(
        lambda x: change_point(
            x["naive.group_main"],
            x["naive.prev_group_main"],
            x["intermediate.prev_duration"],
        ),
        axis=1,
    )

    return res


def get_duration(df, groupby):
    return df.groupby(groupby)["eventSec"].transform(lambda x: x.max() - x.min())


def adjust_episodes(df):
    """
    Adjust the episode number
    """
    res = df.copy()
    res = get_naive_episodes(res)
    res["naive.possession_duration"] = get_duration(res, "naive.episode")
    res = add_change_of_possession(res)

    # why don't we use intermediate.posession_duration?
    res["change_of_possession.long_duration"] = res["change_of_possession"] & (
        res["naive.possession_duration"] > 5
    )
    res["start_of_episode"] = (
        res["obvious.start_of_episode"] | res["change_of_possession.long_duration"]
    )
    res["episode"] = res["start_of_episode"].cumsum()
    return res


def find_first_team_in_naive_episode(group):
    filtered = group[
        (group["type.primary"] == "Pass") | (group["type.primary"] == "Free Kick")
    ]
    if filtered.empty:
        return None
    return filtered.iloc[0]["teamId"]


def find_majority_team_in_episode(group):
    """
    determine the majority of the team who passes the ball
    whichever team has the most passes in the episode is the main team
    """
    filtered = group[
        (group["type.primary"] == "Pass") | (group["type.primary"] == "Free Kick")
    ]

    if filtered.empty:
        return None

    return filtered["teamId"].value_counts().idxmax()


def find_main_team_in_episode(group):
    """
    use either find_first_team_in_naive_episode or find_majority_team_in_episode
    """
    return find_majority_team_in_episode(group)


def change_point(current, previous, previous_duration):
    if previous_duration < 5:
        return False

    if np.isnan(current):
        return False
    if np.isnan(previous):
        return True

    if current is None or previous is None:
        raise ValueError(f"None value in change_point: {current}, {previous}")
    return current != previous


def get_episodes(events, match_info):
    res = []
    events = list(sorted(events, key=lambda x: (x["videoTimestamp"])))
    events_obj = FootballEventFilter(events)
    match_episodes = split_into_episodes(events_obj)
    res.append(match_episodes)
    return pd.concat(res)
