""" Base class for callable commands provider.
"""

from abc import ABC, abstractmethod

from dk.command import CallableCommand


class CallableCommandsProvider(ABC):
    """Provides and executes commands.
    """

    _commands: list[CallableCommand] = []

    def run(self, command_name: str):
        """Run command.
        """
        if not self.supports(command_name):
            raise ValueError("Unsupported command.")

        command = self.get_command(command_name)
        if command.callback:
            command.callback()

    def get_commands(self) -> list[CallableCommand]:
        """Returns the supported commands.
        """
        return self._commands

    def supports(self, command_name: str) -> bool:
        """Returns the information if given command is supported.
        """
        for command in self._commands:
            if command.name == command_name:
                return True
        return False

    def get_command(self, command_name: str) -> CallableCommand:
        """Returns the command.
        """
        for command in self._commands:
            if command.name == command_name:
                return command
        raise ValueError("Unsupported command.")

    @abstractmethod
    def root(self) -> str|None:
        """Return id of the root command this executor provides commands to.
        """

    def _add_command(self, command: CallableCommand) -> None:
        self._commands.append(command)
