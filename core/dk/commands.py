"""Dataclasses for storing commands definitions.
"""

from typing import Callable
from dataclasses import dataclass

@dataclass
class EmptyCommand:
    """Dataclass representing command without any callback.
    """
    name: str
    help: str

@dataclass
class Command(EmptyCommand):
    """Dataclass representing a command.
    """
    callback: Callable[[], None]|None

@dataclass
class ServiceCommand(EmptyCommand):
    """Dataclass representing a service command.
    """
    service: str
    command: str
