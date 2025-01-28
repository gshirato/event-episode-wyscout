import os
import numpy as np
import tqdm
import pandas as pd
import torch
from torch.nn.utils.rnn import pad_sequence
from models.LSTMPredictor import LSTMOneStepPassPredictor
from utils.coordinates import dist
from utils.meta_data import add_team_meta, add_player_meta


def get_padded_episodes(
    data, feature_names, max_len=30, n_episodes=1000, target_names=None
):
    arrays = []
    i = 0
    for (_, _, episode), d in tqdm.tqdm(
        data.groupby(["competition", "match_id", "episode"])
    ):
        # if len of episode is less than max_len, pad it with zeros
        if len(d) < max_len:
            d = pd.concat(
                [
                    pd.DataFrame(
                        np.zeros((max_len - len(d), d.shape[1]), dtype=np.float32),
                        columns=d.columns,
                    ),
                    d,
                ]
            )
        else:
            d = d[-max_len:]

        if target_names is not None:
            combined_data = np.hstack([d[feature_names], d[target_names]])
            arrays.append(combined_data)
        else:
            arrays.append(d[feature_names].values)
        i += 1
        if i > n_episodes:
            break
    if target_names is None:
        width = len(feature_names)
    else:
        width = len(feature_names) + len(target_names)
    arrays = np.array(arrays)
    res = torch.Tensor(arrays).reshape(-1, max_len, width)
    return pad_sequence(res).permute(1, 0, 2)


def create_padded_episodes(
    data, grouped_idx, n_episodes, feature_names, columns, target_names=None
):
    data = filter_groups(data, grouped_idx, columns)

    return get_padded_episodes(
        data, feature_names, n_episodes=n_episodes, target_names=target_names
    )


def filter_groups(df, index, columns):
    res = df.copy()
    res["identifier"] = res[columns].apply(tuple, axis=1)
    res = res[res["identifier"].isin(index)]
    res = res.drop("identifier", axis=1)
    return res


def get_data(competitions, class_name, group_columns, **kwargs):
    root_dir = kwargs.get("root_dir", ".")
    min_event = kwargs.get("min_event", 3)
    max_event = kwargs.get("max_event", 30)
    episodes = pd.read_csv(
        os.path.join(
            root_dir, f"static/csv/{class_name}-episodes-{'-'.join(competitions)}.csv"
        )
    )
    return episodes.groupby(group_columns).filter(
        lambda x: len(x) >= min_event and len(x) <= max_event
    )


def get_dataset(data, feature_names, group_columns):
    groups = list(data.groupby(group_columns).groups.keys())
    n_episodes = len(groups)
    index = groups[: int(n_episodes)]

    dataset = create_padded_episodes(
        data, index, n_episodes, feature_names, group_columns
    )

    return dataset


def get_one_step_pass_predictor(model_path, feature_names, n_hidden):
    model = LSTMOneStepPassPredictor(
        len(feature_names), n_hidden, len(feature_names), feature_names=feature_names
    )

    model.load_state_dict(torch.load(model_path))

    return model


def calculate_losses(groups, y_data, y_hat_data):
    losses = []
    for i, (group, y, y_hat) in enumerate(zip(groups, y_data, y_hat_data)):
        start_dist = dist((y[0:2]), (y_hat[0:2]))
        end_dist = dist((y[2:4]), (y_hat[2:4]))

        losses.append(
            {
                "team_id": group[1].iloc[-1]["team_id"],
                "player_id": group[1].iloc[-1]["player_id"],
                "dist": start_dist + end_dist,
            }
        )

    return pd.DataFrame(losses)


def get_df_losses(data, model, group_columns, team_meta, player_meta):
    index = list(data.groupby(group_columns).groups.keys())
    groups = filter_groups(data, index, group_columns).groupby(group_columns)

    X = model.test_dataset.data[:, :-1, :]
    y = model.test_dataset.data[:, -1, :]
    y_hat, (hn, cn) = model(X)
    df_losses = calculate_losses(groups, y, y_hat)
    df_losses = add_team_meta(df_losses, team_meta)
    df_losses = add_player_meta(df_losses, player_meta)
    return df_losses
