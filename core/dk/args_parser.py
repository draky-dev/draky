"""Argument parser.
"""

import argparse

from dk.argparse_actions import NoAction, ChoicesAction
from dk.commands import EmptyCommand


class ArgsParser:
    """Arguments Parser
    """
    main_parser = None
    commands_parsers = None

    def __init__(self):
        args_parser = argparse.ArgumentParser(prog="dk")
        self.main_parser = args_parser

        args_subparsers = args_parser.add_subparsers(dest='COMMAND')
        self.commands_parsers = args_subparsers

    def register_argument_group(self, name: str, help_text: str, commands: list[EmptyCommand]):
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

    def parse(self, args: list = None):
        """Parse arguments.
        """
        return self.main_parser.parse_known_args(args)[0]

    def add_command(self, command_name, help_text):
        """Add custom command.
        """
        args_parser_customscript = self.commands_parsers.add_parser(
            command_name,
            help=help_text
        )
        args_parser_customscript.add_argument(
            'args',
            nargs=argparse.REMAINDER,
            type=str,
            help="Arguments passed to the script"
        )
