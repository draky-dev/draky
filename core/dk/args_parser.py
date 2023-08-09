"""Argument parser.
"""

import argparse

from dk.argparse_actions import VersionAction
from dk.command import EmptyCommand
from dk.command_provider import CallableCommandsProvider


class ArgsSubparser:
    """Arguments subparser.
    """

    def __init__(self, name: str, argparse_parser: argparse.ArgumentParser = None):
        self._commands: list[str] = []
        self._argparse_parser = argparse_parser
        self._argparse_subparsers = argparse_parser.add_subparsers(dest=name)

    def add_command_group(
        self,
        commands_provider: CallableCommandsProvider,
    ):
        """Register argument group.
        """
        name = commands_provider.name()
        help_text = commands_provider.help_text()
        commands = commands_provider.get_commands()
        argparse_parser = self._argparse_subparsers.add_parser(name, help=help_text)
        parser = ArgsSubparser(name, argparse_parser)

        for command in commands.values():
            if isinstance(command, CallableCommandsProvider):
                parser.add_command_group(command)
                continue
            parser.add_command(command)

        self._commands.append(name)

    def add_command(self, command: EmptyCommand) -> None:
        """Add custom command.
        """
        subparsers = self._argparse_subparsers
        parser = subparsers.add_parser(
            command.name,
            help=command.help
        )
        parser.add_argument(
            command.name,
            nargs=argparse.REMAINDER,
            type=str,
        )

    def add_commands(self, commands: list[EmptyCommand]) -> None:
        """Add a list of commands.
        """
        for command in commands:
            self.add_command(command)

    def has_command(self, name: str) -> bool:
        """Check if first level command with a given name is currently handled.
        """
        return name in self._commands

class ArgsParser(ArgsSubparser):
    """Arguments parser
    """

    def __init__(self, version: str=None):
        super().__init__('COMMAND', argparse.ArgumentParser(prog="dk"))
        self._argparse_parser.add_argument('-v', '--version', action=VersionAction, version=version)
        self._commands = ['-h', '-v', '--version']

    def parse(self, args: list = None):
        """Parse arguments.
        """
        return self._argparse_parser.parse_known_args(args)[0]
