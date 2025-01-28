import json
import os
import time


def save_tsne_results_to_json(tsne_result_list, files, project_dir, conf):
    """
    Converts tsne results to a list and saves them as a JSON file.

    Args:
    - tsne_result_list (list): List containing tsne results.
    - project_dir (str): Directory where the project resides.
    - folder_name (str): Folder name for saving the results.
    - layer_type (str): Type of the layer for the tsne results.

    Returns:
    None
    """

    data = []
    i = conf["base"]["training"]
    for item in tsne_result_list:
        data.append(
            {
                "perplexity": item["perplexity"],
                "tsne_results": item["tsne_results"].tolist(),
                "files": files,
            }
        )
    file_path = os.path.join(
        project_dir,
        "tsne_results",
        f"tsne_result_list_{conf['trainings'][i]['name']}.json",
    )

    with open(file_path, "w") as f:
        json.dump(data, f)


def log_params(logger, conf, i):
    hyperparams = {
        "drawing_type": conf["trainings"][i]["drawing_type"],
        "layer_type": conf["trainings"][i]["model"]["layer_type"],
        "epochs": conf["base"]["epochs"],
        "loss": conf["trainings"][i]["loss"]["name"],
        "optimizer": conf["trainings"][i]["optimizer"]["name"],
        "optimizer_lr": conf["trainings"][i]["optimizer"]["param"]["lr"],
        "max_samples": conf["base"]["max_samples"],
        "batch_size": conf["trainings"][i]["model"]["batch_size"],
    }
    logger.log_hyperparams(hyperparams)


def get_experiment_name(conf, i):
    training = conf["trainings"][i]
    model = conf["trainings"][i]["model"]
    return f"h{model.input_height}xw{model.input_width}-l{model.latent_dim}-bg_{conf.base.bg_color}-{training.loss.name}"


def get_run_name(conf):
    return (
        f"n{conf.base.max_samples}-e{conf.base.epochs}-{time.strftime('%Y%m%d-%H%M%S')}"
    )
