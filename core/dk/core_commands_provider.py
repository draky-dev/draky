""" Provider of the "core" commands.
"""
import sys

from dk.command import CallableCommand
from dk.command_provider import CallableCommandsProvider
from dk.config_manager import ConfigManager


class CoreCommandsProvider(CallableCommandsProvider):
    """This class handles core commands.
    """

    def __init__(self, config_manager: ConfigManager):
        super().__init__()

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
            CallableCommand(
                'internal',
                'Internal endpoint for communication between the draky script and the draky core.',
                self.__internal,
            )
        )

    def root(self) -> str|None:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'core'

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
