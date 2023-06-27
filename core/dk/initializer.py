"""Project initializer.
"""
import os
import sys
import shutil
from dataclasses import dataclass

from colorama import Fore, Style

from dk.config_manager import PATH_PROJECT_CONFIG, PATH_TEMPLATE_DEFAULT, PATH_GLOBAL_CONFIG

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


def __templates_in_path(path_to_parent) -> list[CustomTemplate]:
    """Finds the list of template paths in the given girectory.
    """
    for fname in os.listdir(path_to_parent):
        template_base = os.path.join(path_to_parent, fname)
        template_root = os.path.join(template_base, './.draky')
        if os.path.isdir(template_base) and os.path.isdir(template_root):
            yield CustomTemplate(fname, template_base, template_root)

def initialize():
    """ Function initializing new project. """
    if os.listdir(PATH_PROJECT_CONFIG):
        print(f"{Fore.LIGHTRED_EX}\".drake\" directory already exists in the project and is not "
              f"empty. If you want to initialize the project again, delete it.{Style.RESET_ALL}")
        sys.exit(1)

    project_id = input(f"{Fore.LIGHTBLUE_EX}Enter project id: {Style.RESET_ALL}")
    custom_templates_root_path: str = f"{PATH_GLOBAL_CONFIG}/templates"
    default_template = Template('default', PATH_TEMPLATE_DEFAULT)

    custom_templates: list[Template] = []
    if os.path.exists(custom_templates_root_path):
        custom_templates = __templates_in_path(custom_templates_root_path)

    chosen_template: Template|None = None
    if not custom_templates:
        print(f"{Fore.LIGHTWHITE_EX}No custom templates detected. Using the default one."
              f"{Style.RESET_ALL}")
        chosen_template = default_template

    if not chosen_template:
        print(f"{Fore.LIGHTWHITE_EX}")
        available_templates_map: dict[str, Template] = {
            default_template.name: default_template,
        }
        for custom_template in custom_templates:
            print(f"- {custom_template.name}\n")
            available_templates_map[custom_template.name] = custom_template
        print(f"{Style.RESET_ALL}")

        chosen_template_name = input(f"{Fore.LIGHTBLUE_EX}Enter template name: {Style.RESET_ALL}")
        chosen_template = available_templates_map[chosen_template_name]

    chosen_template_path_draky = f"{chosen_template.path}/.draky"
    shutil.copytree(chosen_template_path_draky, PATH_PROJECT_CONFIG, dirs_exist_ok=True)

    with open(PATH_PROJECT_CONFIG + "/dk.env", "x", encoding='utf8') as file:
        file.write(f"# Do not manually edit this file. It's managed by Draky.\n"
                   f"DRAKY_PROJECT_ID=\"{project_id}\"\n"
                   f"DRAKY_ENVIRONMENT=\"dev\"")
        file.close()

    print(f"{Fore.GREEN}Project has been initialized.{Style.RESET_ALL}")
    sys.exit(0)
