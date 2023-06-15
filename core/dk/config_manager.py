"""Configuration manager.
"""

import os
from dotenv import load_dotenv, dotenv_values

from dk.utils import find_files_weighted_by_filename


class ConfigManager:
    """This class handles everything related to configuration and overall environment.
    """
    # These variables will be empty if we are just initializing the project.
    __project: str|None
    __env: str|None
    __commands_vars: dict = {}

    def init(self):
        """Initialize configuration manager.
        """
        self.__load_environment_variables()
        self.__project = os.environ['DRAKY_PROJECT_ID']\
            if 'DRAKY_PROJECT_ID' in os.environ else None
        self.__env = os.environ['DRAKY_ENVIRONMENT']\
            if 'DRAKY_ENVIRONMENT' in os.environ else None

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

    def __load_environment_variables(self):
        files = find_files_weighted_by_filename("*dk.env", {
            'core.dk.env': -10,
            'cmd.dk.env': 10,
            'local.dk.env': 20,
        }, PATH_PROJECT_CONFIG)
        for path, filename in files:
            path_full = path + '/' + filename
            # @todo We should prefix all variables before loading to exclude any possibility of name
            #       clash with system's env variables, and unexpected behavior that it could cause.

            # We are loading env variables to resolve references.
            load_dotenv(path_full, override=True)

            # Gather cmd vars.
            if filename.endswith('cmd.dk.env'):
                cmd_vars = dotenv_values(path_full)
                command, _, _, _ = filename.split('.')
                if command not in self.__commands_vars:
                    self.__commands_vars[command] = {}
                for cmd_var in cmd_vars:
                    # We assign values that have references already resolved.
                    self.__commands_vars[command][cmd_var] = os.environ[cmd_var]

# We intentionally keep the same project config path as on host. That way docker-compose inside the
# container won't complain that docker-compose.yml file doesn't exist.
PATH_PROJECT_CONFIG = os.environ['DRAKY_PROJECT_CONFIG_ROOT']
PATH_GLOBAL_CONFIG = os.environ['DRAKY_GLOBAL_CONFIG_ROOT']
PATH_COMMANDS = PATH_PROJECT_CONFIG + '/commands'
PATH_ENVIRONMENTS = PATH_PROJECT_CONFIG + '/env'
PATH_TEMPLATE_DEFAULT = '/opt/dk-core/resources/empty-template'
