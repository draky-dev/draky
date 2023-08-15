"""Configuration manager.
"""
import os
import io
from enum import Enum
from typing import Union
from dataclasses import dataclass

import yaml
from dotenv import dotenv_values


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
    def __init__(self, config_type: ConfigType, content: dict):
        self.type: ConfigType = config_type
        self.variables: dict[str, str] = content['variables'] if 'variables' in content else {}
        self.priority: int = content['priority'] if 'priority' in content else 0

@dataclass
class BasicConfig(Config):
    """Dataclass storing the basic config.
    """
    def __init__(self, content: dict):
        super().__init__(ConfigType.BASIC, content)

@dataclass
class AddonConfig(Config):
    """Dataclass storing information about the addons.
    """
    def __init__(self, content: dict):
        super().__init__(ConfigType.ADDON, content)
        self.id = content['id']

@dataclass
class TemplateConfig(Config):
    """Dataclass storing information about the templates.
    """
    def __init__(self, content: dict):
        super().__init__(ConfigType.TEMPLATE, content)
        self.id = content['id']

Configs = Union[BasicConfig, AddonConfig, TemplateConfig]

def fetch_configs(config_path) -> list[Configs]:
    """Returns a list of config objects.
    """
    configs: list[Configs] = []
    for path, _, files in os.walk(config_path):
        for filename in files:
            if not filename.endswith('dk.yml'):
                continue
            with open(f"{path}{os.sep}{filename}", 'r', encoding='utf8') as stream:
                content = yaml.safe_load(stream)
                if filename.endswith('addon.dk.yml'):
                    configs.append(AddonConfig(content))
                elif filename.endswith('template.dk.yml'):
                    configs.append(TemplateConfig(content))
                else:
                    configs.append(BasicConfig(content))
    configs.sort(key=lambda x: x.priority)

    return configs

class ConfigManager:
    """This class handles everything related to configuration and overall environment.
    """

    def __init__(self):
        self.__draky_prefix: str = 'DRAKY_'
        self.__project_data = ProjectData(
            project=None,
            env=None,
            vars={},
            commands_vars={},
            paths=None,
        )
        self.default_template_path: str = '/opt/dk-core/resources/empty-template'

        if 'DRAKY_VERSION' not in os.environ:
            raise ValueError("Required DRAKY_VERSION environment variable is missing.")
        self.version: str = os.environ['DRAKY_VERSION']

        if 'DRAKY_PROJECT_CONFIG_ROOT' not in os.environ:
            return

        # Set helper env variables.
        os.environ['DRAKY_PATH_ADDONS'] = f"{os.environ['DRAKY_PROJECT_CONFIG_ROOT']}/addons"

        # We intentionally keep the same project config path as on host. That way docker-compose
        # inside the container won't complain that docker-compose.yml file doesn't exist.
        project_config_path = os.environ['DRAKY_PROJECT_CONFIG_ROOT']

        if 'DRAKY_GLOBAL_CONFIG_ROOT' not in os.environ:
            raise ValueError("Required DRAKY_PROJECT_CONFIG_ROOT environment variable is missing.")
        self.global_config_path: str = os.environ['DRAKY_GLOBAL_CONFIG_ROOT']

        environments_path = project_config_path + '/env'
        commands_path = project_config_path + '/commands'

        self.__project_data.paths = ProjectPaths(
            project_config=project_config_path,
            environments=environments_path,
            commands=commands_path,
        )

        self.__load_variables()
        # These variables will be empty if we are just initializing the project.
        self.__project_data.project = self.__project_data.vars['DRAKY_PROJECT_ID']\
            if 'DRAKY_PROJECT_ID' in self.__project_data.vars else None
        self.__project_data.env = self.__project_data.vars['DRAKY_ENVIRONMENT']\
            if 'DRAKY_ENVIRONMENT' in self.__project_data.vars else None

    def get_project_paths(self) -> ProjectPaths:
        """Returns object storing project paths.
        """
        if not self.is_project_context():
            raise RuntimeError("Not in the project context.")

        return self.__project_data.paths

    def get_new_project_config_path(self) -> str:
        """Returns project path for
        """
        return self.__project_data.paths.project_config

    def get_project_id(self) -> str|None:
        """Returns current project's id.
        """
        if not self.is_project_context():
            raise RuntimeError("Not in the project context.")

        return self.__project_data.project

    def is_project_context(self) -> bool:
        """Tells if we are running in the project context.
        """
        return bool(self.__project_data.project)

    def get_env(self) -> str|None:
        """Returns current env id.
        """
        if not self.is_project_context():
            raise RuntimeError("Not in the project context.")

        return self.__project_data.env

    def get_command_vars(self, command: str) -> dict:
        """Returns the list of command-related environmental variables.
        """

        if not self.is_project_context():
            return {}

        if command not in self.__project_data.commands_vars:
            return {}
        return self.__project_data.commands_vars[command].copy()

    def get_vars(self) -> dict:
        """Returns a dictionary of currently set environment variables.
        """
        if not self.is_project_context():
            raise RuntimeError("Not in the project context.")

        return self.__project_data.vars

    def __load_variables(self) -> None:
        """Loads variables.
        """
        configs = fetch_configs(self.__project_data.paths.project_config)
        env_content_list: list[str] = []
        # Add to the dictionary all existing variables that start with the prefix.
        env_content_list.append(self.__dict_into_env(
            {k: v for k, v in os.environ.items() if k.startswith(self.__draky_prefix)}
        ))
        for config in configs:
            env_content_list.append(self.__dict_into_env(config.variables))
        self.__project_data.vars = dotenv_values(stream=io.StringIO("\n".join(env_content_list)))

    def __dict_into_env(self, dictionary: dict[str, str]) -> str:
        """Converts the given dictionary into the env string.
        """
        output: str = ''
        for key, value in dictionary.items():
            output += f"{key}={value}\n"
        return output
