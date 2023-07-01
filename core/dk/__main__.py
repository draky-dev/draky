"""Main module
"""

import os
import sys
from colorama import Fore, Style

from dk.args_parser import ArgsParser
from dk.core_commands_provider import CoreCommandsProvider
from dk.env_commands_provider import EnvCommandsProvider
from dk.process_executor import ProcessExecutor
from dk.config_manager import ConfigManager
from dk.custom_commands_provider import CustomCommandsProvider
from dk.initializer import initialize


config_manager = ConfigManager()

process_executor = ProcessExecutor(config_manager)

if config_manager.has_project_switched():
    print("Switching projects.")
    process_executor.env_freeze()
    sys.exit(100)

# If we are initializing, we need to complete initialization before running anything else, as
# therwise config manager won't have enough data.
try:
    if sys.argv[1] == 'env' and sys.argv[2] == 'init':
        initialize(config_manager)
except IndexError:
    pass

args_parser = ArgsParser(version=config_manager.version)

env_commands_provider = EnvCommandsProvider(process_executor)
args_parser.register_argument_group(
    'env', 'Commands for environment management.', env_commands_provider.get_commands()
)
core_commands_provider = CoreCommandsProvider(process_executor)
args_parser.register_argument_group(
    'core', 'Commands for core management.', core_commands_provider.get_commands()
)

custom_commands_provider = CustomCommandsProvider(config_manager)

# Add custom commands to the parser. This is needed for them to be included in the help command.
args_parser.add_commands(custom_commands_provider.get_commands())

# Display help by default.
if len(sys.argv) == 1:
    args_parser.parse(['-h'])

# Only use args_parser for the "env" and "-h" commands. For other commands, pass all arguments
# directly to proper scripts. We are not validating them.
if args_parser.has_first_level_command(sys.argv[1]):
    args = args_parser.parse()
    if sys.argv[1] == env_commands_provider.root():
        # Find all environments.
        available_environments = next(os.walk(config_manager.paths.environments))[1]
        if config_manager.get_env() not in available_environments:
            print(
                f"Environment '{config_manager.get_env()}' has not been found in"
                f" '{config_manager.paths.environments}'."
            )
            sys.exit(1)
        env_commands_provider.run(args.COMMAND)
    elif sys.argv[1] == core_commands_provider.root():
        core_commands_provider.run(args.COMMAND)
    else:
        raise ValueError("Unexpected argument.")

else:
    if not custom_commands_provider.supports(sys.argv[1]):
        print(f"{Fore.RED}Command not found... but you can create it!{Style.RESET_ALL}")
        sys.exit(0)

    custom_command = custom_commands_provider.get_command(sys.argv[1])
    command_file = custom_command.cmd
    service = custom_command.service
    custom_command_name = custom_command.name

    # All reminder arguments, no matter if flags or not.
    reminder_args = sys.argv[2:]
    if service is None:
        command = [command_file] + reminder_args
        process_executor.execute(command)
    else:
        command_variables = config_manager.get_vars()
        process_executor.execute_inside_container(
            service,
            command_file,
            reminder_args,
            command_variables
        )
