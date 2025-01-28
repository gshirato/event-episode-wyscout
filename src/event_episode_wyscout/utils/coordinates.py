import numpy as np


def flip_coordinates(df, team_ids):
    """
    Flip the coordinates for the rows whose team_id is different from the team_id of the episode
    """
    res = df.copy()
    first_team_id = team_ids[0]

    not_first_team = res["team_id"] != first_team_id

    res.loc[not_first_team, "start_x"] = 100 - res.loc[not_first_team, "start_x"]
    res.loc[not_first_team, "end_x"] = 100 - res.loc[not_first_team, "end_x"]
    res.loc[not_first_team, "start_y"] = 100 - res.loc[not_first_team, "start_y"]
    res.loc[not_first_team, "end_y"] = 100 - res.loc[not_first_team, "end_y"]
    return res


def get_coordinates_in_meters(df, precision=2):
    """
    Convert the coordinates from percentage to meters.
    Keep the percentage coordinates in the new columns

    x: 100% = 105m
    y: 100% = 68m
    """
    res = df.copy()

    res["start_x_pct"] = res["start_x"]
    res["start_y_pct"] = res["start_y"]
    res["end_x_pct"] = res["end_x"]
    res["end_y_pct"] = res["end_y"]

    res["start_x"] = (res["start_x"] * 1.05).apply(lambda x: round(x, precision))
    res["start_y"] = ((100 - res["start_y"]) * 0.68).apply(
        lambda x: round(x, precision)
    )
    res["end_x"] = (res["end_x"] * 1.05).apply(lambda x: round(x, precision))
    res["end_y"] = ((100 - res["end_y"]) * 0.68).apply(lambda x: round(x, precision))

    return res


def calculate_distance(df, precision=2):
    res = df.copy()
    res["dx"] = (res["end_x"] - res["start_x"]).apply(lambda x: round(x, precision))
    res["dy"] = (res["end_y"] - res["start_y"]).apply(lambda x: round(x, precision))

    # add the previous end location, filling the first row with start location
    res["prev_end_x"] = res["end_x"].shift(1, fill_value=res["start_x"].iloc[0])
    res["prev_end_y"] = res["end_y"].shift(1, fill_value=res["start_y"].iloc[0])
    res["dist_from_prev"] = np.sqrt(
        (res["start_x"] - res["prev_end_x"]) ** 2
        + (res["start_y"] - res["prev_end_y"]) ** 2
    ).apply(lambda x: round(x, precision))

    return res


def centers_coordinates(df):
    """
    Not used for now.
    Center the coordinates to the center of the pitch
    """
    res = df.copy()
    res["start_x"] = res["start_x"] - 52.5
    res["start_y"] = res["start_y"] - 34
    res["end_x"] = res["end_x"] - 52.5
    res["end_y"] = res["end_y"] - 34
    return res


def dist(p1, p2):
    return (((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5).item()
