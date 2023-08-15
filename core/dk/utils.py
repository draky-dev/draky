"""Utilities.
"""

import os
import pathlib
from fnmatch import fnmatch


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
