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


def show_df(df):
    return df[
        [
            "id",
            "videoTimestamp",
            "type.primary",
            "type.secondary",
            "team.name",
            "location.x.pct",
            "location.y.pct",
            "pass.accurate",
            "shot.isGoal",
        ]
    ]


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

start_events, end_events = segment_events(_event)

cols = st.columns(2)

df["start"] = df["id"].isin(start_events)
df["end"] = df["id"].isin(end_events)
df["start"] = df["start"] | df["end"].shift(1).fillna(True)

df["episode"] = df["start"].cumsum()
st.write(df["episode"].max() + 1)
st.write(df)

team_colors = {"Urawa Reds": "#FF0000", "Tokyo": "#0000FF"}


df["next.location.x.pct"] = df["location.x.pct"].shift(-1)
df["next.location.y.pct"] = df["location.y.pct"].shift(-1)
df["next.team.name"] = df["team.name"].shift(-1)


def draw_episode(df, pitch, fig, ax):
    df = df.copy()
    start_team = df.iloc[0]["team.name"]

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
    return fig


pitch = Pitch(pitch_type="wyscout")

fig, ax = pitch.draw(figsize=(10, 7), constrained_layout=True)

st.selectbox("Select Episode", df["episode"].unique(), index=0, key="episode_select")

for episode in df["episode"].unique():
    episode_data = df[df["episode"] == st.session_state["episode_select"]].copy()
    fig = draw_episode(episode_data, pitch, fig, ax)
    cols = st.columns(2)
    cols[0].pyplot(fig)
    cols[1].write(episode_data)
    break
