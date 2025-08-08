""" Provider of the "__internal" commands.
"""
import sys

from dk.config_manager import BasicConfigManager
from dk.custom_commands_provider import CustomCommandsProvider


class InternalCommandsProvider():
    """Provider of the internal commands.
    """

    def __init__(
            self,
            config_manager: BasicConfigManager,
            custom_command_provider: CustomCommandsProvider,
    ):
        self.config_manager: BasicConfigManager = config_manager
        self.custom_command_provider: CustomCommandsProvider = custom_command_provider

    def handle_internal_commands(self, commands: list) -> None:
        """Handles the internal commands."""
        command = commands[0]
        if command == 'get-project-path':
            self.__print_project_path()
        elif command == 'is-local-command':
            self.__is_local_command(commands[1:])
        elif command == 'get-command-vars':
            self.__print_command_vars()
        sys.exit(0)

    def __print_project_path(self) -> None:
        project_path =\
            self.config_manager.get_project_paths().project_config\
                if self.config_manager.is_project_context()\
                else None
        if project_path:
            print(project_path, end='')

    def __is_local_command(self, _reminder_args: list[str]) -> None:
        command_name = _reminder_args[0]
        if self.custom_command_provider.supports(command_name):
            command = self.custom_command_provider.get_command(command_name)
            if not command.service:
                print(command.cmd, end='')

    def __print_command_vars(self) -> None:
        print(self.config_manager.get_vars_string(), end='')
