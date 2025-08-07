"""Configuration manager.
"""
import os
import io
import re
import sys
from enum import Enum
from typing import Union
from dataclasses import dataclass
from graphlib import TopologicalSorter
from pathlib import Path

import yaml
from dotenv import dotenv_values
from colorama import Fore, Style

@dataclass
class ProjectPaths:
    """Dataclass storing information about paths important for configuration.
    """
    project_config: str
    environments: str
    commands: str

@dataclass
class ProjectData:
    """Dataclass storing information about the current project.
    """
    project: str | None
    env: str | None
    vars: dict[str, str]
    commands_vars: dict | None
    paths: ProjectPaths | None

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

class VariableNotExists(ValueError):
    """This is a helper exception to indicate that variable doesn't exist when requested.
    """
    def __init__(self, name):
        super().__init__(f"Variable {name} doesn't exist.")

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

class BasicConfigManager:
    """Base ConfigManager providing the minimal data required for environment initialization.
    """
    def __init__(self):
        self._draky_prefix: str = 'DRAKY_'
        self._project_data: ProjectData | None = None

        self.default_template_path: str = '/opt/dk-core/resources/empty-template'

        if 'DRAKY_VERSION' not in os.environ:
            raise ValueError("Required DRAKY_VERSION environment variable is missing.")
        self.version: str = os.environ['DRAKY_VERSION']
        self.vars = self.__get_env_variables_dict()
        self._configs = []

        if 'DRAKY_GLOBAL_CONFIG_ROOT' not in os.environ:
            raise ValueError("Required DRAKY_PROJECT_CONFIG_ROOT environment variable is missing.")

        self.global_config_path: str = os.environ['DRAKY_GLOBAL_CONFIG_ROOT']

        if 'DRAKY_PROJECT_CONFIG_ROOT' not in os.environ:
            return

        # We intentionally keep the same project config path as on host. That way docker-compose
        # inside the container won't complain that docker-compose.yml file doesn't exist.
        project_config_path = os.environ['DRAKY_PROJECT_CONFIG_ROOT']

        environments_path = project_config_path + '/env'
        commands_path = project_config_path + '/commands'

        self._project_data = ProjectData(
            project=None,
            env=None,
            vars={},
            commands_vars={},
            paths=ProjectPaths(
                project_config=project_config_path,
                environments=environments_path,
                commands=commands_path,
            ),
        )

    def is_project_context(self) -> bool:
        """Tells if we are running in the project context.
        """
        return bool(self._project_data)

    def get_project_config_path(self) -> str:
        """Returns the project's config path.
        """
        self._ensure_project_context()

        return self._project_data.paths.project_config

    def _ensure_project_context(self):
        if not self.is_project_context():
            raise RuntimeError("Not in the project context.")

    def _dict_into_env(self, dictionary: dict[str, str]) -> str:
        """Converts the given dictionary into the env string.
        """
        output: str = ''
        for key, value in dictionary.items():
            output += f"{key}={value}\n"
        return output

    def _get_env_variables_string(self) -> str:
        return self._dict_into_env(
            {k: v for k, v in os.environ.items() if k.startswith(self._draky_prefix)}
        )

    def __get_env_variables_dict(self) -> dict[str, str]:
        return dotenv_values(stream=io.StringIO(self._get_env_variables_string()))

class ConfigManager(BasicConfigManager):
    """This class handles everything related to configuration and overall environment.
    """

    def __init__(self):
        super().__init__()
        if not self.is_project_context():
            return

        core_config_file_path = Path(f"{self.get_project_config_path()}/core.dk.yml")
        if not core_config_file_path.is_file():
            raise ValueError("Required core.dk.yml file is missing.")

        with core_config_file_path.open(encoding='utf8') as stream:
            core_data = yaml.safe_load(stream)

        if 'variables' not in core_data:
            raise ValueError("Required 'variables' section is missing in core.dk.yml.")

        core_variables = core_data['variables']

        project_id = core_variables['DRAKY_PROJECT_ID']\
            if 'DRAKY_PROJECT_ID' in core_variables else None

        if not project_id:
            raise ValueError("Required DRAKY_PROJECT_ID environment variable is missing.")

        self._project_data.project = project_id

        universal_configs = fetch_configs(self.get_project_config_path())
        universal_variables = self.__get_variables_dict(universal_configs)

        self._project_data.env = self.__get_project_env(universal_variables)
        env = self.get_project_env()
        self._configs = universal_configs + fetch_configs(self.get_project_config_path(), env)

        # Set project vars.
        self._project_data.vars = self.__get_variables_dict(self._configs)
        if self._project_data.env:
            # Make sure that DRAKY_ENV has the up to date value.
            self._project_data.vars['DRAKY_ENV'] = self._project_data.env

    def get_project_paths(self) -> ProjectPaths:
        """Returns object storing project paths.
        """
        self._ensure_project_context()

        return self._project_data.paths

    def get_project_id(self) -> str|None:
        """Returns current project's id.
        """
        self._ensure_project_context()

        return self._project_data.project

    def get_project_env(self) -> str | None:
        """Returns current env id.
        """
        self._ensure_project_context()

        return self._project_data.env

    def get_project_env_path(self) -> str:
        """Returns the path to the current environment directory.
        """
        return f"{self.get_project_paths().environments}/{self.get_project_env()}"

    def get_project_command_vars(self, command: str) -> dict:
        """Returns the list of command-related environmental variables.
        """

        if not self.is_project_context():
            return {}

        if command not in self._project_data.commands_vars:
            return {}
        return self._project_data.commands_vars[command].copy()

    def get_vars(self) -> dict:
        """Returns a dictionary of currently set environment variables.
        """
        if not self.is_project_context():
            return self.vars

        return self._project_data.vars

    def get_vars_string(self) -> str:
        """Returns a string with all currently set environment variables, separated by newlines.
        """
        env_vars = self.get_vars()
        vars_strings: list = []
        for key, value in env_vars.items():
            vars_strings.append(f"{key}={value}")

        return "\n".join(vars_strings)

    def get_addons(self) -> list[AddonConfig]:
        """Returns configuration objects representing addons.
        """
        return list(filter(lambda config: isinstance(config, AddonConfig), self._configs))


    def resolve_vars_in_string(self, string: str) -> str:
        """Replaces vars references with their values in the string.
        """
        found_vars = re.findall(r"\${([A-Z_]+)}", string)
        existing_vars = self.get_vars()
        for var in found_vars:
            if var not in existing_vars:
                raise VariableNotExists(var)
            string = string.replace(f"${{{var}}}", existing_vars[var])

        return string

    def __get_variables_dict(self, configs: list[Config]) -> dict[str, str]:
        """Loads variables.
        """
        env_content_list: list[str] = []
        for config in configs:
            env_content_list.append(self._dict_into_env(config.variables))
        # Add to the dictionary all existing variables that start with the prefix.
        env_content_list.append(self._get_env_variables_string())
        return dotenv_values(stream=io.StringIO("\n".join(env_content_list)))

    def __get_project_env(self, variables: dict[str, str]) -> str | None:
        if not self.is_project_context():
            return None

        return variables['DRAKY_ENV'] if 'DRAKY_ENV' in variables else "dev"

    def filter_configs_by_environment(self, configs: list[Config]) -> list[Config]:
        """Filter configs by environment.
        """
        return [x for x in configs if self.get_project_env() in x.environments]
