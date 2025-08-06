""" Provider of the "env" commands.
"""

from typing import Callable

from dk.command import CallableCommand, Flag
from dk.command_provider import CallableCommandsProvider
from dk.config_manager import ConfigManager
from dk.process_executor import ProcessExecutor

class EnvCommandsProvider(CallableCommandsProvider):
    """This class handles environment commands.
    """

    def __init__(
            self,
            process_executor: ProcessExecutor,
            is_project_context: bool,
            display_help_callback: Callable,
            config_manager: ConfigManager,
    ):
        super().__init__(display_help_callback)
        self.process_executor: ProcessExecutor = process_executor
        self.config_manager: ConfigManager = config_manager

        self._add_command(
            CallableCommand(
                name='init',
                help='Create the environment configuration for the project.',
                callback=None,
            )
        )

        if not is_project_context:
            return

        self.substitute_variables_flag: str = '-s'

        self._add_command(
            CallableCommand(
                name='up',
                help='Start the environment',
                callback=self.__start_environment,
                flags=[
                    Flag(
                        name=self.substitute_variables_flag,
                        help='If the compose file is being build from the recipe, it determines if '
                             'environmental variables should be substituted in the resulting file.',
                        action='store_true',
                    )
                ]
            )
        )

        self._add_command(
            CallableCommand(
                name='stop',
                help='Freeze the environment',
                callback=self.__freeze_environment,
            ),
        )

        self._add_command(
            CallableCommand(
                name='down',
                help='Destroy the environment',
                callback=self.__destroy_environment,
            ),
        )

        self._add_command(
            CallableCommand(
                name='build',
                help='Build the compose file.',
                callback=self.__build_environment,
                flags=[
                    Flag(
                        name=self.substitute_variables_flag,
                        help='Substitute variables with their values.',
                        action='store_true',
                    )
                ]
            )
        )

        self._add_command(
            CallableCommand(
                name='name',
                help='Name of the current environment.',
                callback=self.__name,
            ),
        )

        self._add_command(
            CallableCommand(
                name='compose',
                help='Pass arguments directly to the docker compose.',
                callback=self.__compose,
                add_help=False,
            )
        )

        self._add_command(
            DebugEnvCommandsProvider(config_manager, display_help_callback)
        )

    def name(self) -> str | None:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'env'

    def help_text(self) -> str:
        return 'Environment management.'

    def __start_environment(self, _reminder_args: list[str]):
        """Starts the environment.
        """
        build_flags =\
            [self.substitute_variables_flag] if self.substitute_variables_flag in _reminder_args\
                else []
        self.__build_environment(build_flags)
        self.process_executor.env_start()

    def __freeze_environment(self, _reminder_args: list[str]):
        """Stops the environment.
        """
        self.process_executor.env_freeze()

    def __destroy_environment(self, _reminder_args: list[str]):
        """Destroys the environment.
        """
        self.process_executor.env_destroy()

    def __build_environment(self, _reminder_args: list[str]):
        """Build environment's definition.
        """
        substitute = self.substitute_variables_flag in _reminder_args
        self.process_executor.env_build(substitute)

    def __name(self, _reminder_args: list[str]):
        """Returns the name of the current environment.
        """
        print(self.config_manager.get_env())

    def __compose(self, _reminder_args: list[str]):
        """Pass all arguments to the docker compose.
        """
        self.process_executor.env_compose(_reminder_args)

class DebugEnvCommandsProvider(CallableCommandsProvider):
    """Provides core commands useful for debugging.
    """

    def __init__(self, config_manager: ConfigManager, display_help_callback: Callable):
        super().__init__(display_help_callback)

        self.config_manager: ConfigManager = config_manager

        self._add_command(
            CallableCommand(
                name='vars',
                help="List project's variables.",
                callback=self.__debug_vars,
            )
        )

    def name(self) -> str | None:
        """Gives away information if the current executor supports execution of the given command.
        """
        return 'debug'

    def help_text(self) -> str:
        return 'Debug environment'

    def __debug_vars(self, _reminder_args: list[str]):
        if not self.config_manager.is_project_context():
            print("Variables are available only in the project context")
            return
        #@todo
        variables = self.config_manager.get_vars()
        for variable in variables:
            print(f"{variable} = {variables[variable]}")
