import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Generator, Optional

from core.routers.router import Router


def discover_py_files(directory: str) -> Generator[Path, None, None]:
    """
    Walks through the given directory and yields all .py files that do not start
    with double underscore (__).

    Args:
        directory: The directory to walk in.

    Yields:
        Path: The path to the discovered .py file.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                yield Path(root) / file


def import_module_from_path(path: Path) -> Optional[ModuleType]:
    """
    Imports a Python module from the given path.

    Args:
        path: The path to the .py file to import.

    Returns:
        The imported module, or None if the import failed.
    """
    module_name = path.stem + "_" + str(abs(hash(path)))
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_routers_in_module(module: ModuleType) -> list[Router]:
    """
    Finds all Router instances defined in the given module.

    Args:
        module: The module to search in.

    Returns:
        A list of all Router instances found in the module.
    """
    routers = []
    for attr in dir(module):
        obj = getattr(module, attr)
        if isinstance(obj, Router):
            routers.append(obj)
    return routers
