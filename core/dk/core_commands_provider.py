""" Provider of the "core" commands.
"""
import sys
from typing import Callable

from dk.command import CallableCommand
from dk.command_provider import CallableCommandsProvider
from dk.config_manager import ConfigManager


class CoreCommandsProvider(CallableCommandsProvider):
    """This class handles core commands.
    """

    def __init__(self, config_manager: ConfigManager, display_help_callback: Callable):
        super().__init__(display_help_callback)

        self.config_manager: ConfigManager = config_manager

        self._add_command(
            CallableCommand(
                name='update',
                help='Update draky.',
                callback=self.__update_draky,
            )
        )

        self._add_command(
            CallableCommand(
                name='destroy',
                help='Destroy draky core.',
                callback=None,
            )
        )

        self._add_command(
            CallableCommand(
                name='start',
                help='Start draky core.',
                callback=None,
            )
        )

        self._add_command(
            DebugCommandsProvider(config_manager, display_help_callback)
        )

    def name(self) -> str | None:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'core'

    def help_text(self) -> str:
        return 'draky core management.'

    def __update_draky(self, _reminder_args: list[str]):
        #@todo
        print("To be implemented.")

    @staticmethod
    def get_project_path(config_manager: ConfigManager):
        """Handles the internal command for getting project's path.
        """
        project_path =\
            config_manager.get_project_paths().project_config\
                if config_manager.is_project_context()\
                else None
        if project_path:
            print(project_path, end='')
            sys.exit(0)

class DebugCommandsProvider(CallableCommandsProvider):
    """Provides core commands useful for debugging.
    """

    def __init__(self, config_manager: ConfigManager, display_help_callback: Callable):
        super().__init__(display_help_callback)

        self.config_manager: ConfigManager = config_manager

        self._add_command(
            CallableCommand(
                name='vars',
                help="List project's variables.",
                callback=self.__debug_vars,
            )
        )

    def name(self) -> str | None:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'debug'

    def help_text(self) -> str:
        return 'Debugging'

    def __debug_vars(self, _reminder_args: list[str]):
        if not self.config_manager.is_project_context():
            print("Variables are available only in the project context")
            return
        #@todo
        variables = self.config_manager.get_vars()
        for variable in variables:
            print(f"{variable} = {variables[variable]}")
