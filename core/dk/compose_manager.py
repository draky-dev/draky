"""Tools for building the compose file from the recipe file.
"""
import os
import sys
import typing

import yaml
from colorama import Fore, Style

from dk.config_manager import ConfigManager

class ComposeRecipe:
    """Class representing the compose's recipe.
    """

    def __init__(self, content: dict):
        self.__validate_recipe(content)
        self.__content: dict = content

    def get_addons(self, service: str) -> list[str]:
        """Returns a list of addons for the given service.
        """
        services = self.get_services()
        if service not in services:
            raise ValueError(f"Unknown service '{service}'")
        return services[service]['addons'] if 'addons' in services[service] else []

    def get_services(self) -> dict:
        """Returns the services defined by the recipe.
        """
        return self.__content['services']

    def __validate_recipe(self, content: dict):
        """Validates the recipe's content.
        """
        if 'services' not in content:
            print(
                f"{Fore.RED}The 'services' section is required in the recipe file.{Style.RESET_ALL}"
            )
            sys.exit(1)


class Compose:
    """Class representing the compose file.
    """
    def __init__(
            self, path: str,
            content: dict,
            variables_resolver: callable,
            recipe: ComposeRecipe,
    ):
        self.__path: str = path
        self.__content: dict = content
        self.__variables_resolver: callable = variables_resolver
        self.__substituted_variables: bool = False
        self.__recipe: ComposeRecipe = recipe

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

    def to_string(self) -> str:
        """Returns the content of the compose file as a string.
        """
        compose_string = yaml.safe_dump(self.__content, default_flow_style=False)
        if self.is_substituted_variables():
            compose_string = self.__variables_resolver(compose_string)
        return compose_string

    def list_services(self) -> list:
        """Returns the list of service names.
        """
        if 'services' not in self.__content:
            return []
        return list(self.__content['services'].keys())

    def get_service(self, name: str) -> dict:
        """Returns the dictionary representing the specified service.
        """
        if 'services' not in self.__content or name not in self.__content['services']:
            raise ValueError(f"Service {name} doesn't exist.")
        return self.__content['services'][name]

    def get_recipe(self) -> ComposeRecipe:
        """Returns recipe object that was used to create this compose object.
        """
        return self.__recipe

class ComposeManager:
    """This class is responsible for building a compose file based on the given recipe.
    """

    def __init__(self, config: ConfigManager):
        self.config = config

    def create(self, recipe: ComposeRecipe, recipe_path: str, output_path: str) -> Compose:
        """Creates a compose content from the given recipe.
        :param recipe:
          Dictionary storing the recipe's data.
        :param recipe_path:
           Required for finding the other relatively referenced files.
        :param output_path:
          Required for setting the correct relative paths in volumes in the final compose.
        :return:
          Returns a dictionary representing the final compose.
        """

        compose: dict = {
            'services': {}
        }
        services = recipe.get_services()

        def volume_is_absolute(volume: str) -> bool:
            """Checks if volume is absolute.
            """
            # If volume starts with a variable, then also assume it's absolute.
            return volume.startswith(('/', '${'))

        #def volume_convert_absolute(volume: str) -> str:
        #    """Convert the absolute path into the relative one.
        #    """
        #    return volume.replace(
        #        self.config.get_project_config_path() + os.sep,
        #        os.path.relpath(
        #            self.config.get_project_config_path(), os.path.dirname(output_path)
        #        ) + os.sep
        #    )

        def volume_convert_relative(volume: str, service_path: str) -> str:
            """Change the relative path to keep it relative to the service it came from.
            """
            service_path = os.path.dirname(service_path) \
                            .replace(self.config.get_env_path() + os.sep, '')
            return f"{service_path}/{volume}"

        for service_name in services:
            service_data = services[service_name]

            if 'service' not in service_data:
                raise ValueError(
                    f"'{service_name}' service definition in the recipe is missing the required"
                    f"'content' attribute."
                )

            content = service_data['service']

            service_file_path: str|None = None
            if isinstance(content, str):
                service_file_path = os.path.dirname(recipe_path) + os.sep + content
                with open(service_file_path, "r", encoding='utf8') as f:
                    service_recipe = yaml.safe_load(f)
                service = service_recipe['service']
            elif isinstance(content, dict):
                service = content
            else:
                raise ValueError("Unsupported service reference.")

            # If we are getting the service data from an external file, we need to modify
            # all volumes, so they would still reference the original locations, because the
            # resulting compose file will be in a different location.
            if 'volumes' in service and isinstance(service['volumes'], typing.List):
                for i, _ in enumerate(service['volumes']):
                    volume = service['volumes'][i]
                    service['volumes'][i] =\
                        volume if volume_is_absolute(volume)\
                            else volume_convert_relative(volume, service_file_path)

            # Set up the correct dependencies.
            if 'depends_on' in service_data:
                service['depends_on'] = service_data['depends_on']

            compose['services'][service_name] = service
        return Compose(output_path, compose, self.config.resolve_vars_in_string, recipe)

    def save(self, compose: Compose):
        """Save the compose file to disk.
        """
        with open(compose.get_path(), 'w', encoding='utf8') as f:
            f.write(compose.to_string())
