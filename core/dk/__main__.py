"""Main module
"""

import os
import sys
from colorama import Fore, Style

from dk.args_parser import ArgsParser
from dk.compose_manager import ComposeManager
from dk.core_commands_provider import CoreCommandsProvider
from dk.env_commands_provider import EnvCommandsProvider
from dk.hook_manager import HookManager
from dk.process_executor import ProcessExecutor
from dk.config_manager import ConfigManager
from dk.custom_commands_provider import CustomCommandsProvider
from dk.initializer import initialize


config_manager = ConfigManager()
custom_commands_provider = CustomCommandsProvider(config_manager)

# First we need to handle the "get-project-path" command that may be run before requirements for
# the rest of the core are fulfilled.
if (
    len(sys.argv) == 4
    and sys.argv[1] == 'core'
    and sys.argv[2] == '__internal'
    and sys.argv[3] == 'get-project-path'
):
    CoreCommandsProvider.print_project_path(config_manager)
    sys.exit(0)

# We check if given command is local, because if that's the case, then core has nothing more to do.
if (
    len(sys.argv) >= 5
    and sys.argv[1] == 'core'
    and sys.argv[2] == '__internal'
    and sys.argv[3] == 'is-local-command'
):
    command_name = sys.argv[4]
    if custom_commands_provider.supports(command_name):
        command = custom_commands_provider.get_command(command_name)
        if not command.service:
            print(command.cmd, end='')
    sys.exit(0)

# We check if given command is local, because if that's the case, then core has nothing more to do.
if (
    len(sys.argv) >= 5
    and sys.argv[1] == 'core'
    and sys.argv[2] == '__internal'
    and sys.argv[3] == 'get-command-vars'
):
    command_name = sys.argv[4]
    print(config_manager.get_vars_string(), end='')
    sys.exit(0)


# If we are initializing, we need to complete initialization before running anything else, as
# therwise config manager won't have enough data.
if len(sys.argv) == 3 and sys.argv[1] == 'env' and sys.argv[2] == 'init':
    initialize(config_manager)
    sys.exit(0)

compose_builder = ComposeManager(config_manager)
hook_manager = HookManager(config_manager)
process_executor = ProcessExecutor(config_manager, compose_builder, hook_manager)

args_parser = ArgsParser(version=config_manager.version)

def display_help(arguments=None):
    """Callback displaying help for given arguments.
    """
    if arguments is None:
        arguments = []
    args_parser.parse(arguments + ['-h'])

env_commands_provider = EnvCommandsProvider(
    process_executor,
    config_manager.is_project_context(),
    display_help,
    config_manager,
)
args_parser.add_command_group(env_commands_provider)

core_commands_provider = CoreCommandsProvider(
    display_help,
)
args_parser.add_command_group(core_commands_provider)

# Add custom commands to the parser. This is needed for them to be included in the help command.
args_parser.add_commands(custom_commands_provider.get_commands())

# Display help by default.
if len(sys.argv) == 1:
    display_help()

# Only use args_parser for the "env" and "-h" commands. For other commands, pass all arguments
# directly to proper scripts. We are not validating them.
if args_parser.has_command(sys.argv[1]):
    args = args_parser.parse()
    if not vars(args)[args.COMMAND]:
        args_parser.parse([args.COMMAND, '-h'])
    if sys.argv[1] == env_commands_provider.name():
        # Find all environments.
        available_environments = next(os.walk(config_manager.get_project_paths().environments))[1]
        if config_manager.get_env() not in available_environments:
            print(
                f"Environment '{config_manager.get_env()}' has not been found in"
                f" '{config_manager.get_project_paths().environments}'."
            )
            sys.exit(1)
        env_commands_provider.run(sys.argv[2], sys.argv[3:], sys.argv[1:2])
    elif sys.argv[1] == core_commands_provider.name():
        core_commands_provider.run(sys.argv[2], sys.argv[3:], sys.argv[1:2])
    else:
        raise ValueError("Unexpected argument.")
else:
    if not custom_commands_provider.supports(sys.argv[1]):
        print(f"{Fore.RED}Command not found... but you can create it!{Style.RESET_ALL}")
        sys.exit(0)

    custom_command = custom_commands_provider.get_command(sys.argv[1])
    command_file = custom_command.cmd
    service = custom_command.service

    # All reminder arguments, no matter if flags or not.
    reminder_args = sys.argv[2:]
    variables = config_manager.get_vars()
    if custom_command.service is None:
        raise RuntimeError("This command was supposed to run on host.")

    exit_code = process_executor.execute_inside_container(
        custom_command,
        reminder_args,
        variables
    )
    sys.exit(exit_code)
