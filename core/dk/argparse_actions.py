"""Custom argparse actions.
"""

import argparse


class NoAction(argparse.Action):
    """Class allowing for no-action arguments.
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('default', argparse.SUPPRESS)
        kwargs.setdefault('nargs', 0)
        super().__init__(**kwargs)
        self.required = False

    def __call__(self, parser, namespace, values, option_string=None):
        pass


class ChoicesAction(argparse._StoreAction):  # pylint: disable=protected-access
    """Class providing action that allows for multiple choices.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_choice(self,
                   choice,
                   help=''  # pylint: disable=redefined-builtin
                   ) -> None:
        """
        Adds choice.

        :param choice: Any
        :param help: str
        :return: None
        """
        if self.choices is None:
            self.choices = []
        self.choices.append(choice)
        if hasattr(self, 'container'):
            self.container.add_argument(choice, help=help, action='none')
