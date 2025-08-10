"""Functions for managing application configuration."""

import json
from pathlib import Path
from functions.general import output_path, resource_path

_config = None

def load_config_json(config_file_path_str: str) -> dict:
    """Load the given JSON file and return the resulting object."""
    global _config

    if _config is not None:
        return _config

    config_file_path = Path(resource_path(config_file_path_str))

    with config_file_path.open() as config_file:
        config = json.load(config_file)

    config["paths"]["shifted_cells"] = output_path(config["paths"]["shifted_cells"])
    config["paths"]["output"] = output_path(config["paths"]["output"])

    _config = config

    return config
