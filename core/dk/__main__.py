"""Main module
"""

import os
import sys
from colorama import Fore, Style

from dk.args_parser import ArgsParser
from dk.commands_executor import EnvCommandsExecutor, CoreCommandsExecutor
from dk.process_executor import ProcessExecutor
from dk.config_manager import ConfigManager,\
    PATH_ENVIRONMENTS, PATH_PROJECT_CONFIG, PATH_COMMANDS, DRAKY_VERSION
from dk.custom_commands_provider import provide_custom_commands
from dk.initializer import initialize


config_manager = ConfigManager()

config_manager.init()

process_executor = ProcessExecutor(config_manager)

if config_manager.has_project_switched():
    print("Switching projects")
    process_executor.env_freeze()
    sys.exit(100)

# If we are initializing, we need to complete initialization before running anything else, as
# therwise config manager won't have enough data.
try:
    if sys.argv[1] == 'env' and sys.argv[2] == 'init':
        initialize()
except IndexError:
    pass

args_parser = ArgsParser(version=DRAKY_VERSION)

env_commands_executor = EnvCommandsExecutor(process_executor)
args_parser.register_argument_group(
    'env', 'Commands for environment management.', env_commands_executor.get_commands()
)
core_commands_executor = CoreCommandsExecutor(process_executor)
args_parser.register_argument_group(
    'core', 'Commands for core management.', core_commands_executor.get_commands()
)

# Add custom commands to the parser. This is needed for them to be included in the help command.
custom_commands = provide_custom_commands("*.dk.sh", {
    PATH_COMMANDS: 10,
}, PATH_PROJECT_CONFIG)
for _, custom_command in custom_commands.items():
    args_parser.add_command(custom_command.name, custom_command.help)

# Display help by default.
if len(sys.argv) == 1:
    args_parser.parse(['-h'])

# Only use args_parser for the "env" and "-h" commands. For other commands, pass all arguments
# directly to proper scripts. We are not validating them.
if args_parser.has_first_level_command(sys.argv[1]):
    args = args_parser.parse()
    if sys.argv[1] == env_commands_executor.root():
        # Find all environments.
        available_environments = next(os.walk(PATH_ENVIRONMENTS))[1]
        if config_manager.get_env() not in available_environments:
            print(
                f"Environment '{config_manager.get_env()}' has not been found in"
                f" '{PATH_ENVIRONMENTS}'."
            )
            sys.exit(1)
        env_commands_executor.run(args.COMMAND)
    elif sys.argv[1] == core_commands_executor.root():
        core_commands_executor.run(args.COMMAND)
    else:
        raise ValueError("Unexpected argument.")

else:
    if sys.argv[1] not in custom_commands:
        print(f"{Fore.RED}Command not found... but you can create it!{Style.RESET_ALL}")
        sys.exit(0)

    custom_command = custom_commands[sys.argv[1]]
    command_file = custom_command.command
    service = custom_command.service
    custom_command_name = custom_command.name

    # All reminder arguments, no matter if flags or not.
    reminder_args = sys.argv[2:]
    if service is None:
        command = [command_file] + reminder_args
        process_executor.execute(command)
    else:
        command_variables = config_manager.get_command_vars(custom_command_name)
        process_executor.execute_inside_container(
            service,
            command_file,
            reminder_args,
            command_variables
        )
