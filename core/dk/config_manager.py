"""Configuration manager.
"""
import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from dk.config import Config, AddonConfig, fetch_configs
from dk.utils import vars_dict_from_configs, get_env_vars_dict


@dataclass
class ProjectPaths:
    """Dataclass storing information about paths important for configuration.
    """
    environments: str
    commands: str


class VariableNotExists(ValueError):
    """This is a helper exception to indicate that variable doesn't exist when requested.
    """
    def __init__(self, name):
        super().__init__(f"Variable {name} doesn't exist.")


class ProjectConfigInit:
    """Class representing the project's configuration when it's during the initialization phase.
    """
    config_path: str

    def __init__(self):
        if not ProjectConfigInit.dependencies_are_met():
            raise RuntimeError(
                "Dependencies are not met for the ProjectConfigInit class to be instantiated."
            )

        # We intentionally keep the same project config path as on host. That way docker-compose
        # inside the container won't complain that docker-compose.yml file doesn't exist.
        project_config_path = os.environ['DRAKY_PROJECT_CONFIG_ROOT']

        environments_path = project_config_path + '/env'
        commands_path = project_config_path + '/commands'

        self.config_path = project_config_path
        self.paths = ProjectPaths(
            environments=environments_path,
            commands=commands_path,
        )

    @staticmethod
    def dependencies_are_met() -> bool:
        """Checks if all dependencies related to this project's phase are met.
        """
        return ProjectConfigInit.__get_project_config_path_env_name() in os.environ

    @staticmethod
    def get_project_config_path() -> str:
        """Returns a path to the project's config directory.
        """
        return os.environ[ProjectConfigInit.__get_project_config_path_env_name()]

    @staticmethod
    def __get_project_config_path_env_name():
        return 'DRAKY_PROJECT_CONFIG_ROOT'

class ProjectConfigFull(ProjectConfigInit):
    """Class representing the project's configuration when it's already initialized.
    """

    def __init__(self):
        super().__init__()

        if not ProjectConfigFull.dependencies_are_met():
            raise RuntimeError(
                "Dependencies are not met for the ProjectConfigFull class to be instantiated."
            )

        core_config_file_path = ProjectConfigFull.get_core_config_path()

        with core_config_file_path.open(encoding='utf8') as stream:
            core_data = yaml.safe_load(stream)

        core_variables = core_data['variables']
        project_id = core_variables['DRAKY_PROJECT_ID']

        self.id: str = project_id

        all_configs = fetch_configs(self.config_path)

        universal_configs = [c for c in all_configs if not c.environments]
        universal_variables = vars_dict_from_configs(universal_configs)

        env: str = universal_variables['DRAKY_ENV']\
            if 'DRAKY_ENV' in universal_variables else "dev"

        self.configs: list[Config] = \
            [c for c in all_configs if not c.environments or env in c.environments]

        self.env: str = env

        # Set project vars.
        self.vars: dict[str, str] = vars_dict_from_configs(self.configs)

        # Set helper env variables.
        self.vars['DRAKY_PATH_ADDONS'] = f"{self.config_path}/addons"

        # Make sure that DRAKY_ENV has the up to date value.
        self.vars['DRAKY_ENV'] = self.env

    @staticmethod
    def dependencies_are_met() -> bool:
        """Checks if all dependencies related to this project's phase are met.
        """
        if not ProjectConfigInit.dependencies_are_met():
            return False

        core_config_file_path = ProjectConfigFull.get_core_config_path()
        if not core_config_file_path.is_file():
            return False

        core_config = yaml.safe_load(core_config_file_path.read_text(encoding='utf8'))
        if 'variables' not in core_config:
            raise ValueError("Required 'variables' section is missing in core.dk.yml.")

        if 'DRAKY_PROJECT_ID' not in core_config['variables']:
            raise ValueError("Required DRAKY_PROJECT_ID variable is missing in core.dk.yml.")

        return True

    @staticmethod
    def get_core_config_path() -> Path:
        """Returns a path object pointing to the core.dk.yml file.
        """
        return Path(f"{ProjectConfigInit.get_project_config_path()}/core.dk.yml")

def get_project_config() -> ProjectConfigInit | ProjectConfigFull | None:
    """A factory function returning the appropriate configuration object depending on what
       project data is available.
    """
    if ProjectConfigFull.dependencies_are_met():
        return ProjectConfigFull()

    if ProjectConfigInit.dependencies_are_met():
        return ProjectConfigInit()

    return None

class ConfigManager:
    """This class handles everything related to configuration and overall environment.
    """

    def __init__(self):
        self.project: ProjectConfigInit | ProjectConfigFull | None = get_project_config()

        self.default_template_path: str = '/opt/dk-core/resources/empty-template'

        if 'DRAKY_VERSION' not in os.environ:
            raise ValueError("Required DRAKY_VERSION environment variable is missing.")
        self.version: str = os.environ['DRAKY_VERSION']
        self.vars = get_env_vars_dict()

        if 'DRAKY_GLOBAL_CONFIG_ROOT' not in os.environ:
            raise ValueError("Required DRAKY_PROJECT_CONFIG_ROOT environment variable is missing.")

        self.global_config_path: str = os.environ['DRAKY_GLOBAL_CONFIG_ROOT']


    def get_project_id(self) -> str|None:
        """Returns current project's id.
        """
        self.__ensure_project_context_full()

        return self.project.id

    def get_project_env(self) -> str | None:
        """Returns current env id.
        """
        self.__ensure_project_context_full()

        return self.project.env

    def get_project_env_path(self) -> str:
        """Returns the path to the current environment directory.
        """
        return f"{self.get_project_paths().environments}/{self.get_project_env()}"

    def get_addons(self) -> list[AddonConfig]:
        """Returns configuration objects representing addons.
        """
        self.__ensure_project_context_full()
        return list(filter(lambda config: isinstance(config, AddonConfig), self.project.configs))


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

    def filter_configs_by_environment(self, configs: list[Config]) -> list[Config]:
        """Filter configs by environment.
        """
        return [x for x in configs if self.get_project_env() in x.environments]

    def is_project_context_full(self) -> bool:
        """Tells if we are running in the full project context.
        """
        return isinstance(self.project, ProjectConfigFull)

    def is_project_context_init(self) -> bool:
        """Tells if we are running in the full project context.
        """
        return isinstance(self.project, ProjectConfigInit)

    def is_project_context_none(self) -> bool:
        """Tells if we are running in the full project context.
        """
        return self.project is None

    def get_project_config_path(self) -> str:
        """Returns the project's config path.
        """
        if self.project is None:
            raise RuntimeError("Project config path is not set.")

        return self.project.config_path

    def get_project_paths(self) -> ProjectPaths:
        """Returns object storing project paths.
        """
        self.__ensure_project_context()

        return self.project.paths

    def get_vars(self) -> dict:
        """Returns a dictionary of currently set environment variables.
        """
        if not self.is_project_context_full():
            return self.vars

        return self.project.vars

    def __ensure_project_context_full(self):
        if not self.is_project_context_full():
            raise RuntimeError("Not in the full project context.")

    def __ensure_project_context(self):
        if self.project is None:
            raise RuntimeError("Not in the project context.")
