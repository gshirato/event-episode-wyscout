import streamlit as st

import os
from pathlib import Path
import pandas as pd

from data_container.datasets.event.hudl.fromData import EventFromData
from wyscout_api.logger.setup import setup_logger
from wyscout_api.hudl.handler import APIHandler

from event_episode_wyscout.segment.segment import segment_events

from mplsoccer import Pitch


def flip(row, coord_name, team_name, max_v, start_team):
    if row[team_name] == start_team:
        return row[coord_name]
    return max_v - row[coord_name]


def show_df(df, additional_cols=None):
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


st.set_page_config(
    page_title="Event Data Segmentation",
    page_icon="⚽",
    layout="wide",
)

root_dir = Path(".").resolve()
logger = setup_logger("streamlit", root_dir / "log/streamlit.log")
handler = APIHandler(os.environ["WYSCOUT_ID"], os.environ["WYSCOUT_PW"], logger)

match_id = 5670574
_event = handler.retrieve_event_data(match_id)["events"]
event = EventFromData(pd.DataFrame(_event), fps=25)

df = event.get_data()

start_events, end_events, loose_ball = segment_events(_event)

cols = st.columns(2)


df["loose_ball"] = df["id"].isin(loose_ball)
df["loose_start"] = df["loose_ball"] & (df["loose_ball"].shift(1) != df["loose_ball"])
df["loose_end"] = df["loose_ball"] & (df["loose_ball"].shift(-1) != df["loose_ball"])

df["clear_start"] = df["id"].isin(start_events)
df["clear_end"] = df["id"].isin(end_events) | df["loose_end"]
df["clear_start"] = (
    df["clear_start"] | df["clear_end"].shift(1).fillna(True) | df["loose_start"]
)


df["clear_episode"] = df["clear_start"].cumsum()


with st.expander("Show DataFrame"):
    st.write(df["clear_episode"].max() + 1)
    st.write(df)

team_colors = {"Urawa Reds": "#FF0000", "Tokyo": "#0000FF"}


df["next.location.x.pct"] = df["location.x.pct"].shift(-1)
df["next.location.y.pct"] = df["location.y.pct"].shift(-1)
df["next.team.name"] = df["team.name"].shift(-1)


def draw_episode(df, pitch, fig, ax):
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


inter_start_ids = (
    df.groupby("clear_episode")
    .apply(get_inter_start_ids)
    .set_index("id")["inter.start"]
    .keys()
)
df["inter.start"] = df["id"].isin(inter_start_ids)

df["start"] = df["clear_start"] | df["inter.start"]

df["episode"] = df["start"].cumsum()

pitch = Pitch(pitch_type="wyscout")

fig, ax = pitch.draw(figsize=(10, 7), constrained_layout=True)

st.sidebar.selectbox(
    "Select Episode", df["episode"].unique(), index=0, key="episode_select"
)

episode_data = df[df["episode"] == st.session_state["episode_select"]].copy()
fig = draw_episode(episode_data, pitch, fig, ax)

st.sidebar.pyplot(fig)
st.sidebar.write(episode_data)


for i, episode in enumerate(df["episode"].unique()):
    if i % 3 == 0:
        cols = st.columns(3)
        st.divider()

    pitch = Pitch(pitch_type="wyscout")

    fig, ax = pitch.draw(figsize=(10, 7), constrained_layout=True)

    episode_data = df[df["episode"] == episode].copy()
    fig = draw_episode(episode_data, pitch, fig, ax)
    cols[i % 3].pyplot(fig)
    with cols[i % 3].expander("Episode {}".format(episode)):
        st.write(
            show_df(
                episode_data,
                additional_cols=[
                    "video.duration",
                ],
            )
        )
