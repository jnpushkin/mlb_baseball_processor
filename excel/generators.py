"""Deprecated compatibility wrapper for baseball_processor.excel.generators."""

from importlib import import_module as _import_module
from warnings import warn as _warn

_CANONICAL_MODULE = "baseball_processor.excel.generators"
_warn(
    f"{__name__} is deprecated; use {_CANONICAL_MODULE} instead.",
    DeprecationWarning,
    stacklevel=2,
)
_module = _import_module(_CANONICAL_MODULE)
__all__ = getattr(_module, "__all__", [name for name in dir(_module) if not name.startswith("_")])
globals().update({name: getattr(_module, name) for name in __all__})


def __getattr__(name):
    return getattr(_module, name)


def __dir__():
    return sorted(set(globals()) | set(dir(_module)))
