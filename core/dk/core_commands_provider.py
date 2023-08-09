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
            CallableCommand('update', 'Update draky.', self.__update_draky)
        )

        self._add_command(
            CallableCommand('destroy', 'Destroy draky core.', None)
        )

        self._add_command(
            CallableCommand('start', 'Start draky core.', None)
        )

        self._add_command(
            DebugCommandsProvider(config_manager, display_help_callback)
        )

        self._add_command(
            CallableCommand(
                'internal',
                'Internal endpoint for communication between the draky script and the draky core.',
                self.__internal,
            )
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

    def __internal(self, reminder_args: list[str]):
        if not reminder_args:
            print("Further arguments are required.", file=sys.stderr)
            sys.exit(1)

        if reminder_args[0] == 'get-project-path':
            project_path =\
                self.config_manager.get_project_paths().project_config\
                    if self.config_manager.is_project_context()\
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
            CallableCommand('vars', "List project's variables.", self.__debug_vars)
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
