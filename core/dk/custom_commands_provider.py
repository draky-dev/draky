"""Custom commands provider.
"""

import yaml

from dk.utils import find_files_weighted_by_path
from dk.commands import ServiceCommand

def provide_custom_commands(pattern: str,
                            weights: dict[str, int],
                            root: str) -> dict[str, ServiceCommand]:
    """Provides custom commands.
    """
    command_files = find_files_weighted_by_path(pattern, weights, root)
    custom_commands = {}
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
                help_text = yaml_companion['help'] if yaml_companion and 'help' in yaml_companion \
                    else ''
        except (IOError, yaml.YAMLError):
            pass

        custom_commands[command_name] = ServiceCommand(command_name, help_text, service, full_path)

    return custom_commands
