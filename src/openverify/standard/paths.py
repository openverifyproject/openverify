"""Lexical local path comparisons; no filesystem access or location rewriting."""

import os
from pathlib import Path


def local_path(value: str) -> Path:
    if not value or "\x00" in value:
        raise ValueError("Path must be nonempty and contain no NUL")
    path = Path(value)
    if ".." in path.parts:
        raise ValueError("Parent traversal is not permitted")
    if os.name == "nt" and (bool(path.drive) != bool(path.root)):
        raise ValueError("Windows paths must be relative or fully qualified")
    if os.name == "nt" and os.path.isreserved(value):
        raise ValueError("Reserved or ambiguous Windows path")
    return path


def path_key(value: str) -> Path:
    """Compare native/relative POSIX spellings against the process working directory."""
    return local_path(value).absolute()


def in_directory(target: str, directory: str) -> bool:
    return path_key(target).is_relative_to(path_key(directory))
