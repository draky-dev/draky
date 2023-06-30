"""Configuration manager.
"""

import os
import io
from pathlib import Path
from dotenv import dotenv_values

from dk.utils import find_files_weighted_by_filename


class ConfigManager:
    """This class handles everything related to configuration and overall environment.
    """
    __draky_prefix: str = 'DRAKY_'
    # These variables will be empty if we are just initializing the project.
    __project: str|None
    __env: str|None
    __commands_vars: dict = {}
    __vars: dict[str, str] = {}

    def init(self):
        """Initialize configuration manager.
        """
        self.__load_environment_variables()
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

    def __load_environment_variables(self):
        files = find_files_weighted_by_filename("*dk.env", {
            'core.dk.env': -10,
            'local.dk.env': 10,
        }, PATH_PROJECT_CONFIG)
        vars_list: list = []
        files_content_list: list[str] = []
        for path, filename in files:
            path_full = path + '/' + filename
            files_content_list.append(Path(path_full).read_text(encoding='utf8'))

            # We are loading env variables to resolve references.
            vars_list = vars_list + list(set(dotenv_values(path_full).keys()) - set(vars_list))
        self.__vars = dotenv_values(stream=io.StringIO("\n".join(files_content_list)))

# We intentionally keep the same project config path as on host. That way docker-compose inside the
# container won't complain that docker-compose.yml file doesn't exist.
PATH_PROJECT_CONFIG = os.environ['DRAKY_PROJECT_CONFIG_ROOT']
PATH_GLOBAL_CONFIG = os.environ['DRAKY_GLOBAL_CONFIG_ROOT']
DRAKY_VERSION = os.environ['DRAKY_VERSION']
PATH_COMMANDS = PATH_PROJECT_CONFIG + '/commands'
PATH_ENVIRONMENTS = PATH_PROJECT_CONFIG + '/env'
PATH_TEMPLATE_DEFAULT = '/opt/dk-core/resources/empty-template'
