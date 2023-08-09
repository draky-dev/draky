"""Configuration manager.
"""
import os
import io
from dataclasses import dataclass
import yaml
from dotenv import dotenv_values

from dk.utils import find_files_weighted_by_filename


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
        os.environ['DRAKY_PATH_HELPERS'] = f"{os.environ['DRAKY_PROJECT_CONFIG_ROOT']}/helpers"

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
        files = find_files_weighted_by_filename("*dk.yml", {
            'core.dk.yml': -10,
            'local.dk.yml': 10,
        # Note that we are accessing paths directly, because at this point project context is not
        # determined yet.
        }, self.__project_data.paths.project_config)

        env_content_list: list[str] = []

        # Add to the dictionary all existing variables that start with the prefix.
        env_content_list.append(self.__dict_into_env(
            {k: v for k, v in os.environ.items() if k.startswith(self.__draky_prefix)}
        ))

        for path, filename in files:
            path_full = path + '/' + filename
            with open(path_full, 'r', encoding='utf8') as stream:
                file_content = yaml.safe_load(stream)
                if 'variables' in file_content:
                    variables = file_content['variables']
                    env_content_list.append(self.__dict_into_env(variables))

        self.__project_data.vars = dotenv_values(stream=io.StringIO("\n".join(env_content_list)))

    def __dict_into_env(self, dictionary: dict[str, str]) -> str:
        """Converts the given dictionary into the env string.
        """
        output: str = ''
        for key, value in dictionary.items():
            output += f"{key}={value}\n"
        return output
