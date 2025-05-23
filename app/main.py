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


import pandas as pd


def get_team_percentages(df: pd.DataFrame) -> list:
    """
    attacking actionsの割合を辞書のリストとして返す

    Returns:
        list: [{"team": "チーム名", "count": 回数, "percentage": 割合}, ...]
                データがない場合は空のリスト

    前提:
    最も多いチーム: value_counts()の結果は降順なので、[0]で最頻値を取得
    同数の場合: pandas のvalue_counts()は同じ値の場合、元のデータで先に現れた順序を保持するので、先に出た方が[0]になります

    """
    _df = df.copy()
    actions_with_ball = [
        "pass",
        "touch",
        "goal_kick",
        "throw_in",
        "corner",
        "free_kick",
        "interception",
        "clearance",
        "shot",
    ]
    attacking = _df[_df["type.primary"].isin(actions_with_ball)]

    if attacking.empty:
        return []

    team_counts = attacking["team.name"].value_counts()
    total_actions = team_counts.sum()

    result = []
    for team, count in team_counts.items():
        result.append({"team": team, "count": count, "ratio": count / total_actions})

    return result


def get_is_transition(df: pd.DataFrame) -> bool:
    _df = df.copy()

    if _df.iloc[0]["episode"] == 1:
        return False
    if _df.iloc[0]["clear_start"]:
        return False
    if _df.iloc[0]["prev.episode.team"] == _df.iloc[0]["episode.team"]:
        return False

    return True


def get_is_from_loose_ball(df: pd.DataFrame) -> bool:
    _df = df.copy()
    return _df.iloc[0]["after_loose_end"]


def get_is_to_loose_ball(df: pd.DataFrame) -> bool:
    _df = df.copy()
    return _df.iloc[0]["before_loose_end"]


def make_episode_team_dict_with_offset(episode_team_dict: dict, offset: int) -> dict:
    res = {}
    for episode in sorted(episode_team_dict.keys()):
        offset_episode = episode + offset
        res[episode] = episode_team_dict.get(offset_episode, [])
    return res


def get_episode_duration(df: pd.DataFrame) -> float:
    """
    episodeのdurationを計算する
    """
    _df = df.copy()
    if _df.empty:
        return 0.0
    start_time = _df.iloc[0]["videoTimestamp"]
    end_time = _df.iloc[-1]["videoTimestamp"]
    duration = end_time - start_time
    return duration


def add_episode_info(df: pd.DataFrame) -> pd.DataFrame:
    res = df.copy()

    episode_team_dict = res.groupby("episode").apply(get_team_percentages).to_dict()
    prev_episode_team_dict = make_episode_team_dict_with_offset(episode_team_dict, -1)
    next_episode_team_dict = make_episode_team_dict_with_offset(episode_team_dict, 1)
    res["episode.team.percentage"] = res["episode"].map(episode_team_dict)
    res["episode.team"] = res["episode.team.percentage"].map(
        lambda x: x[0]["team"] if len(x) > 0 else None
    )
    res["prev.episode.team.percentage"] = res["episode"].map(prev_episode_team_dict)
    res["prev.episode.team"] = res["prev.episode.team.percentage"].map(
        lambda x: x[0]["team"] if len(x) > 0 else None
    )
    res["next.episode.team.percentage"] = res["episode"].map(next_episode_team_dict)
    res["next.episode.team"] = res["next.episode.team.percentage"].map(
        lambda x: x[0]["team"] if len(x) > 0 else None
    )

    transition_dict = res.groupby("episode").apply(get_is_transition).to_dict()
    res["episode.is.transition"] = res["episode"].map(transition_dict)

    from_loose_ball_dict = (
        res.groupby("episode").apply(get_is_from_loose_ball).to_dict()
    )
    to_loose_ball_dict = res.groupby("episode").apply(get_is_to_loose_ball).to_dict()
    res["episode.is.to_loose_ball"] = res["episode"].map(to_loose_ball_dict)
    res["episode.is.from_loose_ball"] = res["episode"].map(from_loose_ball_dict)

    episode_duration_dict = res.groupby("episode").apply(get_episode_duration).to_dict()
    res["episode.duration"] = res["episode"].map(episode_duration_dict)

    st.write(res)
    return res


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

df = add_episode_info(df)
df = df[df["type.primary"] != "game_interruption"]

with st.expander("Show DataFrame"):
    st.write(df["clear_episode"].max() + 1)
    st.write(
        df[
            [
                "episode",
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
    "Select Episode", df["episode"].unique(), index=0, key="episode_select"
)

episode_data = df[df["episode"] == st.session_state["episode_select"]].copy()

team_colors = {"Urawa Reds": "#FF0000", "Tokyo": "#0000FF"}
fig = draw_episode(episode_data, pitch, fig, ax, team_colors=team_colors)

st.sidebar.pyplot(fig)
st.sidebar.write(episode_data)

n_shown = 9
episode_start = st.number_input(
    "Episode Start",
    min_value=1,
    max_value=df["episode"].max() - n_shown,
    value=2,
    step=10,
)

for i, episode in enumerate(range(episode_start, episode_start + n_shown)):
    if i % 3 == 0:
        cols = st.columns(3)
        st.divider()

    pitch = Pitch(pitch_type="wyscout")

    fig, ax = pitch.draw(figsize=(10, 7), constrained_layout=True)

    episode_data = df[df["episode"] == episode].copy()
    fig = draw_episode(episode_data, pitch, fig, ax, team_colors)
    cols[i % 3].pyplot(fig)
    with cols[i % 3].expander("Episode {}".format(episode)):
        st.write(
            show_df(
                episode_data,
                additional_cols=[
                    "video.duration",
                    "clear_start",
                ],
            )
        )
