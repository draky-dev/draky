"""Configuration manager.
"""
import os
import io
from dataclasses import dataclass
from pathlib import Path
from dotenv import dotenv_values

from dk.utils import find_files_weighted_by_filename


@dataclass
class ConfigPaths:
    """Dataclass storing information about paths important for configuration.
    """
    project_config: str
    global_config: str
    environments: str
    commands: str
    default_template: str

class ConfigManager:
    """This class handles everything related to configuration and overall environment.
    """
    __draky_prefix: str = 'DRAKY_'
    # These variables will be empty if we are just initializing the project.
    __project: str|None
    __env: str|None
    __commands_vars: dict = {}
    __vars: dict[str, str] = {}

    paths: ConfigPaths
    version: str

    def __init__(self):
        if 'DRAKY_PROJECT_CONFIG_ROOT' not in os.environ:
            raise ValueError("Required DRAKY_PROJECT_CONFIG_ROOT environment variable is missing.")
        # We intentionally keep the same project config path as on host. That way docker-compose
        # inside the container won't complain that docker-compose.yml file doesn't exist.
        project_config_path = os.environ['DRAKY_PROJECT_CONFIG_ROOT']

        if 'DRAKY_GLOBAL_CONFIG_ROOT' not in os.environ:
            raise ValueError("Required DRAKY_PROJECT_CONFIG_ROOT environment variable is missing.")
        global_config_path = os.environ['DRAKY_GLOBAL_CONFIG_ROOT']

        environments_path = project_config_path + '/env'
        commands_path = project_config_path + '/commands'

        self.paths = ConfigPaths(
            project_config=project_config_path,
            global_config=global_config_path,
            environments=environments_path,
            commands=commands_path,
            default_template='/opt/dk-core/resources/empty-template',
        )

        if 'DRAKY_VERSION' not in os.environ:
            raise ValueError("Required DRAKY_VERSION environment variable is missing.")
        self.version = os.environ['DRAKY_VERSION']

        self.__load_variables()
        self.__project = self.__vars['DRAKY_PROJECT_ID']\
            if 'DRAKY_PROJECT_ID' in self.__vars else None
        self.__env = self.__vars['DRAKY_ENVIRONMENT']\
            if 'DRAKY_ENVIRONMENT' in self.__vars else None

        # Add all existing variables that starts with the prefix to the dictionary.
        self.__vars.update(
            {k: v for k, v in os.environ.items() if k.startswith(self.__draky_prefix)}
        )

    @staticmethod
    def has_project_switched() -> bool:
        """Checks if projects has switched.
        """
        return os.environ["DRAKY_PROJECT_CONFIG_CURRENT_ROOT"] \
               != os.environ["DRAKY_PROJECT_CONFIG_ROOT"]

    def get_project_id(self) -> str:
        """Returns current project's id.
        """
        return self.__project

    def get_env(self) -> str:
        """Returns current env id.
        """
        return self.__env

    def get_command_vars(self, command: str) -> dict:
        """Returns the list of command-related environmental variables.
        """
        if command not in self.__commands_vars:
            return {}
        return self.__commands_vars[command].copy()

    def get_vars(self) -> dict:
        """Returns a dictionary of currently set environment variables.
        """
        return self.__vars

    def __load_variables(self):
        files = find_files_weighted_by_filename("*dk.env", {
            'core.dk.env': -10,
            'local.dk.env': 10,
        }, self.paths.project_config)
        vars_list: list = []
        files_content_list: list[str] = []
        for path, filename in files:
            path_full = path + '/' + filename
            files_content_list.append(Path(path_full).read_text(encoding='utf8'))

            # We are loading env variables to resolve references.
            vars_list = vars_list + list(set(dotenv_values(path_full).keys()) - set(vars_list))
        self.__vars = dotenv_values(stream=io.StringIO("\n".join(files_content_list)))
