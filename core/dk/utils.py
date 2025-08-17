"""Utilities.
"""
import io
import os
import pathlib
from fnmatch import fnmatch

from dotenv import dotenv_values

from dk.config import Config


def find_files_weighted_by_path(pattern: str, weights: dict, search_path: str) -> list:
    """Finds list of files matching the given pattern in the given directory.

    :param pattern:
    :param weights:
    :param search_path:
    :return: list
    """
    files_by_weight = {}
    for path, _, files in os.walk(search_path):
        weight = weights.get(path) or 0
        for filename in files:
            if fnmatch(filename, pattern):
                if weight not in files_by_weight:
                    files_by_weight[weight] = []
                files_by_weight[weight].append([path, filename])
    # We are sorting dictionary by keys.
    files_by_weight = {
        key: files_by_weight[key] for key in sorted(files_by_weight.keys())
    }

    files_sorted = []
    for weight, paths in files_by_weight.items():
        for path in paths:
            files_sorted.append(path)

    return files_sorted

def get_path_up_to_project_root(path: str) -> str:
    """Returns the directory structure up the project's root.
    """
    parts = pathlib.PurePath(path).parts
    new_parts = []
    for part in reversed(parts[:-1]):
        new_parts.append(part)
        if part == '.draky':
            break
    return os.sep.join(reversed(new_parts))

def dict_to_env_string(dictionary: dict[str, str]) -> str:
    """Converts the given dictionary into the env string.
    """
    output: str = ''
    for key, value in dictionary.items():
        output += f"{key}={value}\n"
    return output

DRAKY_PREFIX = 'DRAKY_'

def get_env_vars_dict() -> dict[str, str]:
    """Returns a dictionary of draky-related environment variables that are available.
    """
    return {k: v for k, v in os.environ.items() if k.startswith(DRAKY_PREFIX)}

def vars_dict_from_configs(configs: list[Config]) -> dict[str, str]:
    """Loads variables.
    """
    env_content_list: list[str] = []
    for config in configs:
        env_content_list.append(dict_to_env_string(config.variables))
    # Add to the dictionary all existing variables that start with the prefix.
    env_content_list.append(dict_to_env_string(get_env_vars_dict()))
    return dotenv_values(stream=io.StringIO("\n".join(env_content_list)))
