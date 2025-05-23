import pandas as pd


def show_df(df: pd.DataFrame, additional_cols: list[str] | None = None):
    cols = [
        "episode",
        "possession.id",
        "id",
        "type.primary",
        "type.secondary",
        "team.name",
        "player.name",
        "videoTimestamp",
        "location.x.pct",
        "location.y.pct",
        "pass.accurate",
        "shot.isGoal",
        "loose_ball",
        "loose_start",
        "loose_end",
    ] + (additional_cols if additional_cols else [])
    return df[cols]
