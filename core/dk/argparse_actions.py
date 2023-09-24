"""Custom argparse actions.
"""

import argparse

class VersionAction(argparse._VersionAction):  # pylint: disable=protected-access
    """Class providing action for displaying the current version.
    """
