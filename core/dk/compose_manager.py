"""Tools for building the compose file from the recipe file.
"""
import os
import sys
import typing
import copy

import yaml
from colorama import Fore, Style

from dk.config_manager import ConfigManager


class Compose:
    """Class representing the compose file.
    """
    def __init__(
            self,
            path: str,
            content: dict,
            variables_resolver: callable,
    ):
        self.__path: str = path
        self.__content: dict = content
        self.__variables_resolver: callable = variables_resolver
        self.__substituted_variables: bool = False

    def set_substituted_variables(self, value: bool) -> None:
        """Set to true for variables in the compose file to be replaced with their values.
        """
        self.__substituted_variables = value

    def is_substituted_variables(self) -> bool:
        """Tells if compose file should have substituted variables.
        """
        return self.__substituted_variables

    def get_path(self) -> str:
        """Returns the path that indicates where the compose file should be put. It's important
           because it allows relative paths inside the compose file work correctly.
        """
        return self.__path

    def get_service(self, name: str) -> dict:
        """Returns the dictionary representing the specified service.
        """
        if 'services' not in self.__content or name not in self.__content['services']:
            raise ValueError(f"Service {name} doesn't exist.")
        return self.__content['services'][name]

    def list_services(self) -> list:
        """Returns the list of service names.
        """
        if 'services' not in self.__content:
            return []
        return list(self.__content['services'].keys())

    def to_string(self) -> str:
        """Returns the content of the compose file as a string.
        """
        compose_string = yaml.safe_dump(self.__content, default_flow_style=False)
        if self.is_substituted_variables():
            compose_string = self.__variables_resolver(compose_string)
        return compose_string


class ComposeRecipe:
    """Class representing the compose's recipe.
    """

    def __init__(self, content: dict, recipe_path: str, env_path: str):
        self.__validate_recipe(content)
        self.__content: dict = content
        self.recipe_path = recipe_path
        self.__env_path = env_path

    def get_addons(self, service: str) -> list[str]:
        """Returns a list of addons for the given service.
        """
        compose = self.__to_compose_dict(cleaned=False)
        services = compose['services']
        if service not in services:
            raise ValueError(f"Unknown service '{service}'")

        if 'draky' not in services[service]:
            return []

        return services[service]['draky']['addons']\
                    if 'addons' in services[service]['draky'] else []

    def get_services(self) -> dict:
        """Returns the services defined by the recipe.
        """
        return self.__content['services']

    def to_compose(
            self,
            compose_path: str,
            resolve_vars_in_string: callable,
            cleaned: bool = True,
    ) -> Compose:
        """Converts recipe into the compose file.
        """
        compose_dict = self.__to_compose_dict(cleaned)

        return Compose(compose_path, compose_dict, resolve_vars_in_string)

    def __clean_compose(self, compose: dict) -> dict:
        """Removes draky-specific properties from the service's definition.
        """
        if 'services' in compose:
            for service in compose['services']:
                if 'draky' in compose['services'][service]:
                    del compose['services'][service]['draky']

        return compose

    def __to_compose_dict(self, cleaned: bool = True):
        compose_dict = copy.deepcopy(self.__content)
        services = compose_dict['services']

        for service_name in services:
            service_data = services[service_name]

            service = None
            remote_file_path = None

            # Validate the basic structure.
            if 'extends' in service_data:
                extends = service_data['extends']
                self.__validate_extends(service_name, extends)

                remote_file_path = os.path.dirname(self.recipe_path) + os.sep + extends['file']
                if not isinstance(remote_file_path, str):
                    raise ValueError(
                        f"Error in the '{service_name}' service. The 'file' value has to be a "
                        f"string."
                    )

                if 'service' not in extends:
                    raise ValueError(
                        f"Error in the '{service_name}' service. The 'service' value is required "
                        f"if the service extends another service."
                    )
                remote_file_service = extends['service']
                if not isinstance(remote_file_service, str):
                    raise ValueError(
                        f"Error in the '{service_name}' service. The 'service' value has to be "
                        f"a string."
                    )

                with open(remote_file_path, "r", encoding='utf8') as f:
                    remote_file_dict = yaml.safe_load(f)

                self.__validate_service_in_extended_compose(remote_file_service, remote_file_dict)

                if not isinstance(remote_file_dict['services'][remote_file_service], dict):
                    raise ValueError(
                        f"Error in the '{service_name}' service. The service"
                        f"'{remote_file_service}' in the '{remote_file_path}' file has to be a "
                        f"dictionary."
                    )

                del service_data['extends']
                service = remote_file_dict['services'][remote_file_service] | service_data

            if not service:
                service = service_data

            # If we are getting the service data from an external file, we need to modify
            # all volumes, so they would still reference the original locations, because the
            # resulting compose file will be in a different location.
            if 'volumes' in service and isinstance(service['volumes'], typing.List):
                for i, _ in enumerate(service['volumes']):
                    volume = service['volumes'][i]
                    service['volumes'][i] =\
                        volume if self.__volume_is_absolute(volume)\
                            else self.__volume_convert_relative(volume, remote_file_path)

            compose_dict['services'][service_name] = service

        if cleaned:
            return self.__clean_compose(compose_dict)

        return compose_dict

    def __volume_is_absolute(self, volume: str) -> bool:
        """Checks if volume is absolute.
        """
        # If volume starts with a variable, then also assume it's absolute.
        return volume.startswith(('/', '${'))

    def __volume_convert_relative(self, volume: str, service_path: str) -> str:
        """Change the relative path to keep it relative to the service it came from.
        """
        service_path = os.path.dirname(service_path).replace(self.__env_path + os.sep, '')
        return f"{service_path}/{volume}"

    def __validate_recipe(self, content: dict):
        """Validates the recipe's content.
        """
        if 'services' not in content:
            print(
                f"{Fore.RED}The 'services' section is required in the recipe file.{Style.RESET_ALL}"
            )
            sys.exit(1)

    def __validate_extends(self, service_name: str,  extends: dict) -> None:
        if not isinstance(extends, dict):
            raise ValueError(
                f"Error in the '{service_name}' service. 'extends' key has to be a "
                f"dictionary."
            )
        if 'file' not in extends:
            raise ValueError(
                f"Error in the '{service_name}' service. The 'file' value is required if "
                f"the service extends another service."
            )

    def __validate_service_in_extended_compose(self, service_name: str, compose: dict) -> None:
        if 'services' not in compose or service_name not in compose['services']:
            raise ValueError(f"Error in the '{service_name}' service. It's missing in the "
                             f"extended compose file.")

class ComposeManager:
    """This class is responsible for building a compose file based on the given recipe.
    """

    def __init__(self, config: ConfigManager):
        self.config = config

    def create(self, recipe: ComposeRecipe, compose_path: str) -> Compose:
        """Creates a compose content from the given recipe.
        :param recipe:
          Dictionary storing the recipe's data.
        :param recipe_path:
           Required for finding the other relatively referenced files.
        :param compose_path:
          Required for setting the correct relative paths in volumes in the final compose.
        :return:
          Returns a dictionary representing the final compose.
        """

        return recipe.to_compose(compose_path, self.config.resolve_vars_in_string)

    def save(self, compose: Compose):
        """Save the compose file to disk.
        """
        with open(compose.get_path(), 'w', encoding='utf8') as f:
            f.write(compose.to_string())
