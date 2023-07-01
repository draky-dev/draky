""" Provider of the "env" commands.
"""

from dk.command import CallableCommand
from dk.command_provider import CallableCommandsProvider
from dk.process_executor import ProcessExecutor


class EnvCommandsProvider(CallableCommandsProvider):
    """This class handles environment commands.
    """
    process_executor: ProcessExecutor

    def __init__(self, process_executor: ProcessExecutor):
        self.process_executor = process_executor

        self._add_command(
            CallableCommand('up', 'Start the environment', self.process_executor.env_start)
        )

        self._add_command(
            CallableCommand('stop', 'Freeze the environment', self.process_executor.env_freeze)
        )

        self._add_command(
            CallableCommand('down', 'Destroy the environment', self.process_executor.env_destroy)
        )

        self._add_command(
            CallableCommand(
                'init',
                'Create the environment configuration for the project.',
                None,
            )
        )

    def root(self) -> str|None:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'env'
