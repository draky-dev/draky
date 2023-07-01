""" Provider of the "core" commands.
"""

from dk.command import CallableCommand
from dk.command_provider import CallableCommandsProvider
from dk.process_executor import ProcessExecutor


class CoreCommandsProvider(CallableCommandsProvider):
    """This class handles core commands.
    """
    process_executor: ProcessExecutor

    def __init__(self, process_executor: ProcessExecutor):
        self.process_executor = process_executor

        self._add_command(
            CallableCommand('update', 'Update draky.', self._update_draky)
        )

        self._add_command(
            CallableCommand('destroy', 'Destroy draky core.', None)
        )

        self._add_command(
            CallableCommand('start', 'Start draky core.', None)
        )

    def root(self) -> str|None:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'core'

    def _update_draky(self):
        #@todo
        print("To be implemented.")
