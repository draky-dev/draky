"""Classes storing different types of configuration, and helper functions related to them.
"""
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from graphlib import TopologicalSorter
from typing import Union

import yaml
from colorama import Fore, Style


class ConfigType(Enum):
    """Available configuration types.
    """
    BASIC = 'basic'
    ADDON = 'addon'
    TEMPLATE = 'template'


@dataclass
class Config:
    """Dataclass storing information about a single config file.
    """
    def __init__(self, config_type: ConfigType, content: dict, path: str):
        self.id: str = content['id'] if 'id' in content else path
        self.type: ConfigType = config_type
        self.variables: dict[str, str] = content['variables'] if 'variables' in content else {}
        self.dependencies: list[str] = content['dependencies'] if 'dependencies' in content else []
        self.environments: list[str] = content['environments'] if 'environments' in content else []
        self.path: str = path
        self.dirpath: str = os.path.dirname(path)


@dataclass
class BasicConfig(Config):
    """Dataclass storing the basic config.
    """
    def __init__(self, content: dict, path: str):
        super().__init__(ConfigType.BASIC, content, path)


@dataclass
class AddonConfig(Config):
    """Dataclass storing information about the addons.
    """
    def __init__(self, content: dict, path: str):
        super().__init__(ConfigType.ADDON, content, path)
        self.id = content['id']


@dataclass
class TemplateConfig(Config):
    """Dataclass storing information about the templates.
    """
    def __init__(self, content: dict, path: str):
        super().__init__(ConfigType.TEMPLATE, content, path)
        self.id = content['id']


Configs = Union[BasicConfig, AddonConfig, TemplateConfig]


def fetch_configs(config_path, env: str | None = None) -> list[Configs]:
    """Returns a list of config objects. If no "env" is provided, then only universal configs are
       returned.
    """
    configs: list[Configs] = []
    for path, _, files in os.walk(config_path):
        for filename in files:
            if not filename.endswith('dk.yml'):
                continue
            with open(f"{path}{os.sep}{filename}", 'r', encoding='utf8') as stream:
                content = yaml.safe_load(stream)
                trimmed_path = re.sub(r'^.*?\.draky', '', path)
                config_path = f"{trimmed_path}{os.sep}{filename}".lstrip(os.sep)

                if filename.endswith('addon.dk.yml'):
                    config = AddonConfig(content, config_path)
                elif filename.endswith('template.dk.yml'):
                    config = TemplateConfig(content, config_path)
                else:
                    config = BasicConfig(content, config_path)

                if env and env not in config.environments:
                    continue

                if not env and config.environments:
                    continue
            configs.append(config)

    sort_configs_by_dependencies(configs)

    return configs


def sort_configs_by_dependencies(configs: list[Configs]):
    """Sorts a list of configs by dependencies.
    """
    ids: list[str] = [item.id for item in configs]
    unmet_dependencies: list[tuple[str, str]] = []
    for config in filter(lambda c: c.dependencies, configs):
        unmet_dependencies_list = filter(lambda d: d not in ids, config.dependencies)
        for dep in unmet_dependencies_list:
            unmet_dependencies.append((dep, config.path))

    if unmet_dependencies:
        print(f"{Fore.RED}[ERROR] The following dependencies are unmet:", file=sys.stderr)
        for dep in unmet_dependencies:
            print(f"'{dep[0]}' in '{dep[1]}'", file=sys.stderr)
        print(Style.RESET_ALL, file=sys.stderr)
        sys.exit(1)

    # Create a dictionary with dependencies only.
    depmap: dict[str, list[str]] = {}
    for config in configs:
        depmap[config.id] = config.dependencies

    sorter = TopologicalSorter(depmap)
    configs_backup = configs.copy()
    configs.clear()
    for config_id in sorter.static_order():
        config = next((x for x in configs_backup if x.id == config_id), None)
        if not config:
            raise RuntimeError("Could not find the config object. "
                               "The logic of sorting configs by dependencies must be flawed.")
        configs.append(config)
