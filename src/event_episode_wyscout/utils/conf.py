import os
from omegaconf import OmegaConf


def load_competition_conf(root_dir: str, competition: str):
    base = OmegaConf.load(os.path.join(root_dir, "src/configs", "base.yaml"))
    comp = OmegaConf.load(
        os.path.join(root_dir, "src/configs/competitions", f"{competition}.yaml")
    )
    return OmegaConf.merge(base, comp)
