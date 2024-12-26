""" Provider of the "core" commands.
"""
from typing import Callable

from dk.command import CallableCommand
from dk.command_provider import CallableCommandsProvider


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
