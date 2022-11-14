from omegaconf import OmegaConf


def read_config(path: str):
    conf = OmegaConf.load(path)
    return conf


