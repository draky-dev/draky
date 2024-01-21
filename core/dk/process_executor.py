"""Process executor. Executes other processes.
"""

import os
import sys
import pathlib
from subprocess import Popen, PIPE, run, DEVNULL

import yaml

from dk.compose_manager import ComposeManager, ComposeRecipe
from dk.config_manager import ConfigManager
from dk.hook_manager import HookManager
from dk.utils import get_path_up_to_project_root


class ProcessExecutor:
    """Class handling execution of system processes.
    """

    def __init__(
            self,
            config: ConfigManager,
            compose_manager: ComposeManager,
            hook_manager: HookManager,
    ) -> None:
        self.config: ConfigManager = config
        self.compose_manager: ComposeManager = compose_manager
        self.hook_manager: HookManager = hook_manager
        self.stdin_passed: bool = False

    def get_command_base(self) -> list:
        """Returns beginning of every command.
        """
        return [
            'docker',
            'compose',
            '-p',
            f"{self.config.get_project_id()}",
            '-f',
            self.__get_compose_path(),
        ]

    def env_build(self, substitute_vars: bool = False):
        """Build the environment's definition.
        """
        recipe_path = self.__get_recipe_path()
        if os.path.exists(recipe_path):
            with open(recipe_path, "r", encoding='utf8') as f:
                recipe_content = yaml.safe_load(f)
            recipe = ComposeRecipe(recipe_content)
            compose = self.compose_manager.create(recipe, recipe_path, self.__get_compose_path())
            compose.set_substituted_variables(substitute_vars)
            self.hook_manager.addon_alter_services(compose)
            self.compose_manager.save(compose)

    def env_start(self) -> None:
        """Start environment.
        """
        command = self.get_command_base()
        command.extend(['up', '-d'])
        self.execute(command)

    def env_freeze(self) -> None:
        """Freezes environment.
        """
        command = self.get_command_base()
        command.extend(['stop'])
        self.execute(command)

    def env_destroy(self) -> None:
        """Destroys environment.
        """
        command = self.get_command_base()
        command.extend(['down', '-v'])
        self.execute(command)

    def execute(self, command: list, pass_stdin: bool = False, container: bool = False) -> None:
        """Executes given command.
        """
        if pass_stdin:
            if self.stdin_passed:
                raise ValueError("stdin has already been used up")
            self.stdin_passed = True
        # If we are not passing stdin, we need to pass "DEVNULL" if we execute this command in
        # a container, and "None" if we run this command on host.
        # For some reason if that's not the case, stdin isn't available either in the script in
        # the container, or on the host.
        # @todo Figure out why that's the case and write an explanation here.
        stdin = sys.stdin if pass_stdin else DEVNULL if container else None
        run(command, check=False, stdin=stdin, env=self.config.get_vars())

    def execute_pipe(
            self,
            commands: list,
            previous_process: Popen[bytes] | Popen[str | bytes] = None,
            pass_stdin: bool = False
    ) -> None:
        """Executes chain of commands and pipes output from the previous one, to the next one.
        """
        first_command = commands.pop(0)
        stdout = PIPE if commands else sys.stdout
        default_stdin = None
        if pass_stdin:
            if self.stdin_passed:
                raise ValueError("stdin has already been used up")
            self.stdin_passed = True
            default_stdin = sys.stdin

        stdin = previous_process.stdout if previous_process else default_stdin

        with Popen(
            first_command, stdout=stdout, stderr=sys.stderr, stdin=stdin, env=self.config.get_vars()
        ) as process:
            if commands:
                self.execute_pipe(commands, process)

    def execute_inside_container(
            self,
            service: str,
            script_path: str,
            reminder_args: list,
            variables=None
    ) -> None:
        """Executes given script in a given service's container.

        :param variables:
        :param service:
        :param script_path:
        :param reminder_args:
        :return:
        """
        script_path_with_draky_root = get_path_up_to_project_root(script_path)
        if variables is None:
            variables = {}
        # Destination is constant.
        dest_path = f"/tmp/{script_path_with_draky_root}"
        dest = f"{dest_path}/{pathlib.PurePath(script_path).name}"
        # Prepare the dir path for the script to be copied.
        mkdir_command = self.get_command_base()
        mkdir_command.extend(['exec', '-T', service, 'mkdir',  '-p', dest_path])
        self.execute(mkdir_command, False, True)

        # Copy script into container to avoid having to pipe commands, as that would disable
        # coloring.
        copy_command = self.get_command_base()
        copy_command.extend([
            'exec', '-T', service, 'sh', '-c', f"cat > {dest} < /dev/stdin;chmod a+x {dest}"
        ])
        self.execute_pipe([['cat', script_path], copy_command])

        # Run the script by using docker's "exec" command.
        command = self.get_command_base()
        command.extend(['exec'])

        # Pass the variables to the container running the command.
        for var in variables:
            command.extend(['-e', var])
        if not sys.stdin.isatty():
            command.extend(['-T'])
        command.extend([service, dest])
        command.extend(reminder_args)
        self.execute(command, True, True)

    def __get_recipe_path(self) -> str:
        return f"{self.config.get_env_path()}/docker-compose.recipe.yml"

    def __get_compose_path(self) -> str:
        return f"{self.config.get_env_path()}/docker-compose.yml"
