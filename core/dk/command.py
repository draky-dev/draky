"""Dataclasses for storing commands definitions.
"""

from typing import Callable
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Flag:
    """Command's flag.
    """
    name: str
    help: str
    action: str = field(default_factory=lambda: 'store')


@dataclass(kw_only=True)
class EmptyCommand:
    """Dataclass representing command without any callback.
    """
    name: str
    help: str
    flags: list[Flag] = field(default_factory=lambda: [])
    add_help: bool = True


@dataclass(kw_only=True)
class CallableCommand(EmptyCommand):
    """Dataclass representing a command.
    """
    callback: Callable[[list], None]|None


@dataclass(kw_only=True)
class ServiceCommand(EmptyCommand):
    """Dataclass representing a service command.
    """
    service: str|None
    cmd: str
    user: str = '0'
