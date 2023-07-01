"""Process executor. Executes other processes.
"""

import sys
import pathlib
from subprocess import Popen, PIPE, run, DEVNULL

from dk.config_manager import ConfigManager
from dk.utils import get_path_up_to_project_root


class ProcessExecutor:
    """Class handling execution of system processes.
    """
    config: ConfigManager

    stdin_passed: bool = False

    def __init__(self, config: ConfigManager) -> None:
        self.config = config

    def get_command_base(self) -> list:
        """Returns beginning of every command.

        :return: list
        """
        return [
            'docker',
            'compose',
            '-p',
            f"{self.config.get_project_id()}",
            '-f',
            f"{self.config.paths.environments}/{self.config.get_env()}/docker-compose.yml"
        ]

    def env_start(self) -> None:
        """Start environment.

        :return: None
        """
        command = self.get_command_base()
        command.extend(['up', '-d'])
        self.execute(command)

    def env_freeze(self) -> None:
        """Freezes environment.

        :return: None
        """
        command = self.get_command_base()
        command.extend(['stop'])
        self.execute(command)

    def env_destroy(self) -> None:
        """Destroys environment.

        :return:
        """
        command = self.get_command_base()
        command.extend(['down', '-v'])
        self.execute(command)

    def execute(self, command: list, pass_stdin: bool = False) -> None:
        """Executes given command.
        """
        if pass_stdin:
            if self.stdin_passed:
                raise ValueError("stdin has already been used up")
            self.stdin_passed = True
        stdin = sys.stdin if pass_stdin else DEVNULL
        run(command, check=False, stdin=stdin, env=self.config.get_vars())

    def execute_pipe(
            self,
            commands: list,
            previous_process:Popen[bytes] | Popen[str | bytes] = None,
            pass_stdin: bool = False
    ) -> None:
        """Executes chain of commands and pipes output from the previous one, to the next one.
        """
        first_command = commands.pop(0)
        stdout = PIPE if commands else sys.stdout
        default_stdin = DEVNULL
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
        self.execute(mkdir_command)

        # Copy script into container to avoid having to pipe commands, as that would disable
        # coloring.
        copy_command = self.get_command_base()
        copy_command.extend([
            'exec', '-T', service, 'bash', '-c', f"cat > {dest} < /dev/stdin;chmod a+x {dest}"
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
        self.execute(command, True)
