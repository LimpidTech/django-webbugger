"""Django Webbugger - A tracking beacon library for Django applications."""

from __future__ import annotations

__version__ = "1.0.0"


def __getattr__(name: str):
    """Lazy import to avoid Django app registry issues during testing."""
    if name == "trackable":
        from .models import trackable
        return trackable
    if name == "Beacon":
        from .models import Beacon
        return Beacon
    if name == "IP":
        from .models import IP
        return IP
    if name == "IPEntity":
        from .models import IPEntity
        return IPEntity
    if name == "trigger":
        from .views import trigger
        return trigger
    if name == "create_beacon":
        from .views import create_beacon
        return create_beacon
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "__version__",
    "Beacon",
    "create_beacon",
    "IP",
    "IPEntity",
    "trackable",
    "trigger",
]
