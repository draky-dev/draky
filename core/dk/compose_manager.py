"""Tools for building the compose file from the recipe file.
"""
import os
import sys
import typing
import copy

import yaml
from colorama import Fore, Style
from packaging import version

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

        compose_string = ('# This file is autogenerated because the environment contains a '
                          'recipe. To modify the services, modify the recipe.\n') + compose_string
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

        extended_files: dict = self.__gather_extended_files(services)
        compose_dict = self.__merge_top_level_values(compose_dict, extended_files)

        # Handle services.
        for service_name in services:
            service_data = services[service_name]

            service = None
            remote_file_path = None

            # Validate the basic structure.
            if 'extends' in service_data:
                extends = service_data['extends']
                remote_file_path = os.path.dirname(self.recipe_path) + os.sep + extends['file']
                remote_file_service = extends['service']
                if not isinstance(remote_file_service, str):
                    raise ValueError(
                        f"Error in the '{service_name}' service. The 'service' value has to be "
                        f"a string."
                    )

                if remote_file_path not in extended_files:
                    with open(remote_file_path, "r", encoding='utf8') as f:
                        extended_files[remote_file_path] = yaml.safe_load(f)

                remote_file_dict = extended_files[remote_file_path]

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

            service = self.__convert_paths_in_service(service, compose_dict, remote_file_path)
            compose_dict['services'][service_name] = service

        if cleaned:
            return self.__clean_compose(compose_dict)

        return compose_dict

    def __convert_paths_in_service(
            self,
            service: dict,
            compose_dict: dict,
            remote_file_path: str,
    ) -> dict:
        # If we are getting the service data from an external file, we need to modify
        # all volumes, so they would still reference the original locations, because the
        # resulting compose file will be in a different location.
        if 'volumes' in service and isinstance(service['volumes'], typing.List):
            for i, _ in enumerate(service['volumes']):
                volume = service['volumes'][i]
                if not self.__volume_is_named(volume, compose_dict):
                    service['volumes'][i] =\
                        volume if self.__volume_is_absolute(volume)\
                            else self.__volume_convert_relative(volume, remote_file_path)

        if 'build' in service and isinstance(service['build'], dict):
            build = service['build']
            if 'dockerfile' in build and isinstance(build['dockerfile'], str):
                dockerfile_path = build['dockerfile']
                build['dockerfile'] =\
                  dockerfile_path if self.__path_is_absolute(dockerfile_path)\
                    else self.__path_convert_relative(dockerfile_path, remote_file_path)

        return service

    def __gather_extended_files(self, services: dict) -> dict:
        """Gathers the values of all files extended in the recipe.
        """

        extended_files: dict = {}

        # Gather the extended files.
        for service_name in services:
            service_data = services[service_name]

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

                if remote_file_path not in extended_files:
                    with open(remote_file_path, "r", encoding='utf8') as f:
                        extended_files[remote_file_path] = yaml.safe_load(f)

        return extended_files

    def __merge_top_level_values(self, compose: dict, extended_files: dict) -> dict:
        """Merges values from the extended files into the resulting compose file.
        """
        # Merge other top level values from the extended files into the compose file.
        for _, extended_file in extended_files.items():
            for top_level_key in extended_file:
                # Services have been already handled.
                if top_level_key == 'services':
                    continue

                top_level_value = extended_file[top_level_key]
                if top_level_key not in compose:
                    compose[top_level_key] = top_level_value
                else:
                    compose[top_level_key] = self.__merge_top_level_value(
                        top_level_key,
                        top_level_value,
                        compose[top_level_key],
                    )
        return compose

    def __volume_is_absolute(self, volume: str|dict) -> bool:
        """Checks if volume is absolute.
        """
        path = volume if isinstance(volume, str) else volume['source']
        return self.__path_is_absolute(path)

    def __volume_is_named(self, volume: str|dict, compose: dict) -> bool:
        """Checks if volume is named.
        """
        if isinstance(volume, str):
            volume_splitted = volume.split(':')
            if len(volume_splitted) == 0:
                raise ValueError("Incorrect volumes string format")
            path = volume.split(':')[0]
        else:
            path = volume['source']

        if 'volumes' in compose:
            if not isinstance(compose['volumes'], dict):
                return False
            if path in compose['volumes'].keys():
                return True
        return False

    def __volume_convert_relative(self, volume: str|dict, service_path: str) -> str|dict:
        """Change the relative path to keep it relative to the service it came from.
        """
        if isinstance(volume, str):
            return self.__path_convert_relative(volume, service_path)
        volume['source'] = self.__path_convert_relative(volume['source'], service_path)
        return volume

    def __path_convert_relative(self, path: str, service_path: str) -> str:
        return os.path.dirname(service_path).replace(self.__env_path + os.sep, '')\
                + os.sep + path

    def __path_is_absolute(self, path: str) -> bool:
        # If path starts with a variable, then also assume it's absolute.
        return path.startswith(('/', '${'))

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

    def __merge_top_level_value(self, name: str, new_value, existing_value):
        """Merges top-level compose values.
        """
        # We want to get the highest version.
        if name == 'version':
            return new_value if version.parse(new_value) > version.parse(existing_value)\
                else existing_value
        return existing_value | new_value

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
