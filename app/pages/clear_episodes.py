import streamlit as st

import os
from pathlib import Path

from wyscout_api.logger.setup import setup_logger
from wyscout_api.hudl.handler import APIHandler


from mplsoccer import Pitch
from episode_split.visualization.draw import draw_episode
from episode_split.visualization.dataframe import show_df
from episode_split.episode.split import process


@st.cache_data
def load_data(_handler, match_id):
    return process(
        handler=_handler,
        match_id=match_id,
    )


st.set_page_config(
    page_title="Event Data Segmentation",
    page_icon="⚽",
    layout="wide",
)

root_dir = Path(".").resolve()
logger = setup_logger("streamlit", root_dir / "log/streamlit.log")
handler = APIHandler(os.environ["WYSCOUT_ID"], os.environ["WYSCOUT_PW"], logger)


cols = st.columns(2)

df = load_data(handler, match_id=5670574)


with st.expander("Show DataFrame"):
    st.write("\# Clear episodes", df["clear_episode"].max() + 1)
    st.write(
        df[
            [
                "episode",
                "clear_episode",
                "matchPeriod",
                "videoTimestamp",
                "type.primary",
                "type.secondary",
                "team.name",
                "player.name",
            ]
        ]
    )


pitch = Pitch(pitch_type="wyscout")

fig, ax = pitch.draw(figsize=(10, 7), constrained_layout=True)

st.sidebar.selectbox(
    "Select Clear Episode", df["clear_episode"].unique(), index=0, key="episode_select"
)


episode_data = df[df["clear_episode"] == st.session_state["episode_select"]].copy()

team_colors = {"Urawa Reds": "#FF0000", "Tokyo": "#0000FF"}
fig = draw_episode(episode_data, pitch, fig, ax, team_colors=team_colors)

st.sidebar.pyplot(fig)
st.sidebar.write(episode_data)

n_shown = 6
episode_start = st.number_input(
    "Clear Episode Start",
    min_value=1,
    max_value=df["clear_episode"].max() - n_shown,
    value=2,
    step=10,
)

for i, episode in enumerate(range(episode_start, episode_start + n_shown)):
    if i % 3 == 0:
        cols = st.columns(3)
        st.divider()

    pitch = Pitch(pitch_type="wyscout")

    fig, ax = pitch.draw(figsize=(10, 7), constrained_layout=True)

    episode_data = df[df["clear_episode"] == episode].copy()
    fig = draw_episode(episode_data, pitch, fig, ax, team_colors)
    cols[i % 3].pyplot(fig)
    with cols[i % 3].expander("Clear Episode {}".format(episode)):
        st.write(
            episode_data[
                [
                    "clear_episode",
                    "team.name",
                    "type.primary",
                    "matchPeriod",
                    "videoTimestamp",
                    "type.secondary",
                    "player.name",
                    "episode",
                ]
            ]
            # show_df(
            #     episode_data,
            #     additional_cols=[
            #         "episode.team",
            #         "episode.duration",
            #         "clear_start",
            #     ],
            # )
        )
    if cols[i % 3].button(
        "Copy dataframe to clipboard",
        key=f"copy_{episode}",
    ):
        episode_data.to_clipboard(index=False)
        cols[i % 3].success("DataFrame copied to clipboard!")
