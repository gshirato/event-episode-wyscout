import pandas as pd


def get_intermediate_start(df_episode: pd.DataFrame) -> pd.Series:
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


def get_inter_start_ids(df: pd.DataFrame) -> pd.DataFrame:
    res = df[df["type.secondary"].map(lambda x: "defensive_duel" not in x)]
    if res.empty:
        return pd.DataFrame(columns=["id", "inter.start"])

    res["change.team"] = res["team.name"].shift(1) != res["team.name"]
    res["small.episode"] = res["change.team"].cumsum()
    duration = res.groupby("small.episode")["video.duration"].sum().to_dict()
    count = res.groupby("small.episode")["id"].count().to_dict()
    res["small.episode.duration"] = res["small.episode"].map(duration)
    res["small.episode.count"] = res["small.episode"].map(count)

    res["inter.start"] = get_intermediate_start(res)
    return res[res["inter.start"]]


def is_score_in_df(df):
    attack_team = df["team.name"].values[0]
    shots = df[df["type.primary"] == "shot"]
    if shots.empty:
        return False

    if shots.iloc[-1]["team.name"] != attack_team:
        return False
    if df["possession.attack.withGoal"].values.any():
        return True
    if df["type.secondary"].map(lambda x: "goal_conceded" in x).any():
        return True
    return False


def is_shot_in_df(df):
    attack_team = df["team.name"].values[0]
    shots = df[df["type.primary"] == "shot"]
    if shots.empty:
        return False

    if shots.iloc[-1]["team.name"] != attack_team:
        return False
    if df["possession.attack.withShot"].values.any():
        return True
    if df["type.secondary"].map(lambda x: "goal_conceded" in x).any():
        return True
    return False


def is_shot_in_df_against(df):
    attack_team = df["team.name"].values[0]
    shots = df[df["type.primary"] == "shot"]
    if shots.empty:
        return False

    if shots.iloc[-1]["team.name"] == attack_team:
        return False
    if df["possession.attack.withShot"].values.any():
        return True
    if df["type.secondary"].map(lambda x: "goal_conceded" in x).any():
        return True
    return False


def is_goal_against_in_df(df):
    attack_team = df["team.name"].values[0]
    shots = df[df["type.primary"] == "shot"]
    if shots.empty:
        return False

    if shots.iloc[-1]["team.name"] == attack_team:
        return False
    if df["possession.attack.withGoal"].values.any():
        return True
    if df["type.secondary"].map(lambda x: "goal_conceded" in x).any():
        return True
    return False
