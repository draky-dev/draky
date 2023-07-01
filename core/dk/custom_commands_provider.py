"""Custom commands provider.
"""

import yaml

from dk.config_manager import ConfigManager
from dk.utils import find_files_weighted_by_path
from dk.command import ServiceCommand


class CustomCommandsProvider:
    """Provider of the custom commands.
    """

    config_manager: ConfigManager

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def supports(self, command_name: str) -> bool:
        """Returns the information if given command is supported.
        """
        custom_commands = self.__gather_custom_commands()
        for command in custom_commands:
            if command.name == command_name:
                return True
        return False

    def get_commands(self) -> list[ServiceCommand]:
        """Returns the supported commands.
        """
        return self.__gather_custom_commands()

    def get_command(self, command_name: str) -> ServiceCommand:
        """Returns the command.
        """
        commands = self.__gather_custom_commands()
        for command in commands:
            if command.name == command_name:
                return command
        raise ValueError("Unsupported command.")

    def __gather_custom_commands(self) -> list[ServiceCommand]:
        command_files = find_files_weighted_by_path("*.dk.sh", {
            self.config_manager.paths.commands: 10,
        }, self.config_manager.paths.project_config)

        custom_commands = []
        for path, filename in command_files:
            filename_split = list(reversed(filename.split('.')))
            filename_sections_count = len(filename_split)
            if filename_sections_count < 3 or filename_sections_count > 4:
                continue

            command_name = filename_split[filename_sections_count - 1]
            service = filename_split[filename_sections_count - 2] if filename_sections_count == 4 \
                else None
            full_path = path + '/' + filename

            # Find yaml companion.
            help_text = ''
            try:
                with open(full_path + ".yml", "r", encoding='utf8') as stream:
                    yaml_companion = yaml.safe_load(stream)
                    help_text = yaml_companion['help']\
                        if yaml_companion and 'help' in yaml_companion else ''
            except (IOError, yaml.YAMLError):
                pass

            custom_commands.append(ServiceCommand(command_name, help_text, service, full_path))

        return custom_commands
