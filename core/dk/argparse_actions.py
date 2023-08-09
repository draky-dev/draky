"""Custom argparse actions.
"""

import argparse

class VersionAction(argparse._VersionAction):  # pylint: disable=protected-access,too-few-public-methods
    """Class providing action for displaying the current version.
    """
