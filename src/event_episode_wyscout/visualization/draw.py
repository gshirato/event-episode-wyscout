import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch


def flip(
    row: pd.Series, coord_name: str, team_name: str, max_v: float, start_team: str
) -> float:
    if row[team_name] == start_team:
        return row[coord_name]
    return max_v - row[coord_name]


def draw_episode(
    df: pd.DataFrame,
    pitch: Pitch,
    fig: plt.Figure,
    ax: plt.Axes,
    team_colors: dict[str, str],
) -> pd.DataFrame:
    df = df.copy()
    start = df.iloc[0]
    start_team = start["team.name"]

    end = df.iloc[-1]

    df["location.x.pct"] = df.apply(
        lambda row: flip(row, "location.x.pct", "team.name", 100, start_team), axis=1
    )
    df["location.y.pct"] = df.apply(
        lambda row: flip(row, "location.y.pct", "team.name", 100, start_team), axis=1
    )

    df["next.location.x.pct"] = df.apply(
        lambda row: flip(row, "next.location.x.pct", "next.team.name", 100, start_team),
        axis=1,
    )
    df["next.location.y.pct"] = df.apply(
        lambda row: flip(row, "next.location.y.pct", "next.team.name", 100, start_team),
        axis=1,
    )

    pitch.scatter(
        df["location.x.pct"],
        df["location.y.pct"],
        ax=ax,
        facecolor="none",
        edgecolor=df["team.name"].map(team_colors),
        s=100,
        lw=1,
    )

    pitch.arrows(
        df["location.x.pct"],
        df["location.y.pct"],
        df["next.location.x.pct"],
        df["next.location.y.pct"],
        ax=ax,
        color=df["team.name"].map(team_colors),
        width=2,
    )

    for i, row in df.iterrows():
        pitch.annotate(
            row["type.primary"],
            xy=(row["location.x.pct"], row["location.y.pct"] + 2),
            ax=ax,
            color="black",
            fontsize=10,
            ha="center",
            va="center",
        )

    ax.set_title(
        "Episode {} - {} - ({:02d}:{:02d} - {:02d}:{:02d})".format(
            start["episode"],
            start["team.name"],
            int(start["minute"]),
            int(start["second"]),
            int(end["minute"]),
            int(end["second"]),
        ),
        fontsize=16,
    )
    return fig
