"""Project initializer.
"""
import os
import sys
import shutil
from typing import Generator
from dataclasses import dataclass

from colorama import Fore, Style

from dk.config_manager import ConfigManager


@dataclass
class Template:
    """Dataclass storing information about the template.
    """
    name: str
    path: str

@dataclass
class CustomTemplate(Template):
    """Dataclass storing information about the custom template.
    """
    path_base: str


def __templates_in_path(path_to_parent) -> Generator[CustomTemplate, None, None]:
    """Finds the list of template paths in the given girectory.
    """
    for fname in os.listdir(path_to_parent):
        template_base = os.path.join(path_to_parent, fname)
        template_root = os.path.join(template_base, './.draky')
        if os.path.isdir(template_base) and os.path.isdir(template_root):
            yield CustomTemplate(fname, template_base, template_root)

def initialize(config_manager: ConfigManager):
    """ Function initializing new project. """

    project_config_path: str = config_manager.get_new_project_config_path()

    if os.listdir(project_config_path):
        print(f"{Fore.LIGHTRED_EX}\".drake\" directory is not empty. "
              f"If you want to initialize the project again, delete it.{Style.RESET_ALL}")
        sys.exit(1)

    project_id = input(f"{Fore.LIGHTBLUE_EX}Enter project id: {Style.RESET_ALL}")
    custom_templates_root_path: str = f"{config_manager.global_config_path}/templates"
    default_template = Template('default', config_manager.default_template_path)

    custom_templates: list[Template] = []
    if os.path.exists(custom_templates_root_path):
        custom_templates = list(__templates_in_path(custom_templates_root_path))

    chosen_template: Template|None = None
    if not custom_templates:
        print(f"{Fore.LIGHTWHITE_EX}No custom templates detected. Using the default one."
              f"{Style.RESET_ALL}")
        chosen_template = default_template

    if not chosen_template:
        print(f"{Fore.LIGHTWHITE_EX}")
        available_templates_map: dict[str, Template] = {}
        available_templates: list[Template] = [default_template] + custom_templates
        for index, template in enumerate(available_templates):
            print(f"[{index}]: {template.name}")
            available_templates_map[str(index)] = template
        print(f"{Style.RESET_ALL}")
        chosen_template_number =\
            input(f"{Fore.LIGHTBLUE_EX}Enter template number: {Style.RESET_ALL}")
        chosen_template = available_templates_map[chosen_template_number]

    chosen_template_path_draky = f"{chosen_template.path}/.draky"
    shutil.copytree(
        chosen_template_path_draky,
        project_config_path,
        dirs_exist_ok=True
    )

    with open(
            project_config_path + "/core.dk.env", "x", encoding='utf8'
    ) as file:
        file.write(f"# Do not manually edit this file. It's managed by Draky.\n"
                   f"DRAKY_PROJECT_ID=\"{project_id}\"\n"
                   f"DRAKY_ENVIRONMENT=\"dev\"")
        file.close()

    print(f"{Fore.GREEN}Project has been initialized.{Style.RESET_ALL}")
    sys.exit(0)
