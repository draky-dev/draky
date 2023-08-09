""" Base class for callable commands provider.
"""
from abc import ABC, abstractmethod
from typing import Union, Callable

from dk.command import CallableCommand


class CallableCommandsProvider(ABC):
    """Provides and executes commands.
    """

    def __init__(self, display_help_callback: Callable):
        self.__commands: dict[str, Union[CallableCommand, "CallableCommandsProvider"]] = {}
        self.__display_help_callback: Callable = display_help_callback

    def run(self, command_name: str, reminder_args: list[str], previous_args: list[str] = None):
        """Run command.
        """
        if not command_name:
            self.__display_help_callback(previous_args)

        if not self.supports(command_name):
            raise ValueError("Unsupported command.")

        command = self.get_command(command_name)
        if isinstance(command, CallableCommandsProvider):
            previous_args = previous_args + [command_name]
            command_name = reminder_args.pop(0) if reminder_args else None
            command.run(command_name, reminder_args, previous_args)
            return

        if command.callback:
            command.callback(reminder_args)

    def get_commands(self) -> dict[str, Union[CallableCommand, "CallableCommandsProvider"]]:
        """Returns the supported commands.
        """
        return self.__commands

    def supports(self, command_name: str) -> bool:
        """Returns the information if given command is supported.
        """
        return command_name in self.get_commands()

    def get_command(self, command_name: str) -> Union[CallableCommand, "CallableCommandsProvider"]:
        """Returns the command.
        """
        commands = self.get_commands()
        if not command_name in commands:
            raise ValueError("Unsupported command.")

        return commands[command_name]

    @abstractmethod
    def name(self) -> str | None:
        """Return id of the root command this executor provides commands to.
        """

    @abstractmethod
    def help_text(self) -> str:
        """Help text describing this group of commands.
        """

    def _add_command(self, command: Union[CallableCommand, "CallableCommandsProvider"]) -> None:
        if isinstance(command, CallableCommandsProvider):
            self.__commands[command.name()] = command
            return

        self.__commands[command.name] = command
