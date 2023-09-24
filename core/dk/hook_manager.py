"""Manager of hooks allowing for hooking into the draky to modify its behavior.
"""
import os
from importlib import util

from dk.compose_manager import Compose
from dk.config_manager import ConfigManager


class HookUtils:
    """Utilities for hooks.
    """
    def __init__(self, config: ConfigManager):
        self.__config: ConfigManager = config

    def substitute_variables(self, string: str) -> str:
        """Substitute variables in the given string.
        """
        return self.__config.resolve_vars_in_string(string)


class HookManager:
    """Manages hooks that can be externally invoked.
    """

    def __init__(self, config: ConfigManager):
        self.__config: ConfigManager = config
        self.__utils = HookUtils(config)

    def addon_alter_services(self, compose: Compose):
        """Allows addons to alter services.
        """
        services = compose.list_services()
        addons = self.__config.get_addons()
        recipe = compose.get_recipe()

        for addon in addons:

            for service in services:
                service_addons = recipe.get_addons(service)
                if addon.id not in service_addons:
                    continue

                addon_path = addon.path
                addon_path_absolute =(
                        self.__config.get_project_config_path() +
                        os.sep +
                        os.path.dirname(addon_path)
                )

                hooks_path = addon_path_absolute + os.sep + 'hooks.py'
                if not os.path.exists(hooks_path):
                    continue
                spec = util.spec_from_file_location('', hooks_path)
                module = util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'alter_service'):
                    service_data = compose.get_service(service)
                    module.alter_service(
                        service,
                        service_data,
                        self.__utils,
                        addon
                    )
