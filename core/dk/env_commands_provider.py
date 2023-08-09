""" Provider of the "env" commands.
"""

from typing import Callable

from dk.command import CallableCommand
from dk.command_provider import CallableCommandsProvider
from dk.process_executor import ProcessExecutor

class EnvCommandsProvider(CallableCommandsProvider):
    """This class handles environment commands.
    """

    def __init__(
            self,
            process_executor: ProcessExecutor,
            is_project_context: bool,
            display_help_callback: Callable,
    ):
        super().__init__(display_help_callback)
        self.process_executor: ProcessExecutor = process_executor

        self._add_command(
            CallableCommand(
                'init',
                'Create the environment configuration for the project.',
                None,
            )
        )

        if not is_project_context:
            return

        self._add_command(
            CallableCommand('up', 'Start the environment', self.__start_environment)
        )

        self._add_command(
            CallableCommand('stop', 'Freeze the environment', self.__freeze_environment)
        )

        self._add_command(
            CallableCommand('down', 'Destroy the environment', self.__destroy_environment)
        )

    def name(self) -> str | None:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'env'

    def help_text(self) -> str:
        return 'Environment management.'

    def __start_environment(self, _reminder_args: list[str]):
        """Starts the environment.
        """
        self.process_executor.env_start()

    def __freeze_environment(self, _reminder_args: list[str]):
        """Stops the environment.
        """
        self.process_executor.env_freeze()

    def __destroy_environment(self, _reminder_args: list[str]):
        """Destroys the environment.
        """
        self.process_executor.env_destroy()
