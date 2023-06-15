"""Core commands.
"""
from dk.commands import Command, EmptyCommand

from dk.process_executor import ProcessExecutor

class EnvCommandsExecutor:
    """This class handles core commands.
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

def get_core_commands() -> list[EmptyCommand]:
    """Returns core commands.
    """
    commands: dict[str, EmptyCommand] = {}

    commands['up'] =\
        EmptyCommand('up', 'Start the environment')
    commands['stop'] =\
        EmptyCommand('stop','Freeze the environment')
    commands['down'] =\
        EmptyCommand('down', 'Destroy the environment')

    return list(commands.values())
