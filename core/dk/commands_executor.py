"""Core commands.
"""

from abc import ABC, abstractmethod

from dk.commands import Command
from dk.process_executor import ProcessExecutor

class CommandExecutor(ABC):
    """Provides and executes commands.
    """

    @abstractmethod
    def run(self, command_name: str):
        """Run command.
        """

    @abstractmethod
    def get_commands(self) -> list[Command]:
        """Returns the supported commands.
        """

    @abstractmethod
    def root(self) -> str:
        """Return id of the root command this executor provides commands to.
        """


class EnvCommandsExecutor(CommandExecutor):
    """This class handles environment commands.
    """
    process_executor: ProcessExecutor
    commands: dict[str, Command] = {}

    def __init__(self, process_executor: ProcessExecutor):
        self.process_executor = process_executor

        self.commands['up'] =\
            Command('up', 'Start the environment', self.process_executor.env_start)
        self.commands['stop'] =\
            Command('stop', 'Freeze the environment', self.process_executor.env_freeze)
        self.commands['down'] =\
            Command('down', 'Destroy the environment', self.process_executor.env_destroy)
        self.commands['init'] =\
            Command(
                'init',
                'Create the environment configuration for the project.',
                None,
            )

    def run(self, command_name: str):
        """Run core command.
        """
        if command_name not in self.commands:
            raise ValueError("Unsupported env command.")

        command = self.commands.get(command_name)
        if command.callback:
            command.callback()

    def get_commands(self) -> list[Command]:
        """Returns the supported core commands.
        """
        return list(self.commands.values())

    def root(self) -> str:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'env'


class CoreCommandsExecutor(CommandExecutor):
    """This class handles core commands.
    """
    process_executor: ProcessExecutor
    commands: dict[str, Command] = {}

    def __init__(self, process_executor: ProcessExecutor):
        self.process_executor = process_executor
        self.commands['update'] = Command('update', 'Update draky.', self._update_draky)
        self.commands['destroy'] = Command('destroy', 'Destroy draky core.', None)
        self.commands['start'] = Command('start', 'Start draky core.', None)

    def run(self, command_name: str):
        """Run core command.
        """
        if command_name not in self.commands:
            raise ValueError("Unsupported env command.")

        command = self.commands.get(command_name)
        command.callback()

    def get_commands(self) -> list[Command]:
        """Returns the supported core commands.
        """
        return list(self.commands.values())

    def root(self) -> str:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'core'

    def _update_draky(self):
        #@todo
        print("To be implemented.")
