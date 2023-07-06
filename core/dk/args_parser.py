"""Argument parser.
"""

import argparse

from dk.argparse_actions import NoAction, ChoicesAction, VersionAction
from dk.command import CallableCommand, EmptyCommand


class ArgsParser:
    """Arguments Parser
    """

    def __init__(self, version:str=None):
        args_parser = argparse.ArgumentParser(prog="dk")
        args_parser.add_argument('-v', '--version', action=VersionAction, version=version)
        self.main_parser = args_parser

        args_subparsers = args_parser.add_subparsers(dest='COMMAND')
        self.commands_parsers = args_subparsers
        self.first_level_commands = ['-h', '-v', '--version']

    def register_argument_group(self, name: str, help_text: str, commands: list[CallableCommand]):
        """Register argument group.
        """
        args_parser = self.commands_parsers.add_parser(name, help=help_text)
        args_parser.register('action', 'none', NoAction)
        args_parser.register('action', 'store_choice', ChoicesAction)
        group = args_parser.add_argument_group()
        commands_arg = group.add_argument(
            'COMMAND',
            metavar='COMMAND',
            action='store_choice',
            help='Description'
        )
        for command in commands:
            commands_arg.add_choice(command.name, help=command.help)
        self.first_level_commands.append(name)

    def parse(self, args: list = None):
        """Parse arguments.
        """
        return self.main_parser.parse_known_args(args)[0]

    def add_command(self, command: EmptyCommand) -> None:
        """Add custom command.
        """
        args_parser_customscript = self.commands_parsers.add_parser(
            command.name,
            help=command.help
        )
        args_parser_customscript.add_argument(
            'args',
            nargs=argparse.REMAINDER,
            type=str,
            help="Arguments passed to the script"
        )

    def add_commands(self, commands: list[EmptyCommand]) -> None:
        """Add a list of commands.
        """
        for command in commands:
            self.add_command(command)

    def has_first_level_command(self, name: str) -> bool:
        """Check if first level command with a given name is currently handled.
        """
        return name in self.first_level_commands
