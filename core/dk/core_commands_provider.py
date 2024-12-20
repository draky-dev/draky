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

    def __init__(self, display_help_callback: Callable):
        super().__init__(display_help_callback)

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
    def print_project_path(config_manager: ConfigManager) -> None:
        """Handles the internal command for getting project's path.
        """
        project_path =\
            config_manager.get_project_paths().project_config\
                if config_manager.is_project_context()\
                else None
        if project_path:
            print(project_path, end='')
            sys.exit(0)
