from __future__ import annotations
import warnings
import importlib.metadata

from .common import *
from .lib import get_library_files, load_librtlsdr

PYRTLSDR_MIN_VERSION = '0.3.0'

class VersionWarning(UserWarning):
    pass


def check_pyrtlsdr_version():
    def parse_version(version: str) -> list[int]:
        return [int(v) for v in version.split('.')]
    def normalize_version(a: list[int], b: list[int]) -> tuple[list[int], list[int]]:
        len_a, len_b = len(a), len(b)
        if len_a < len_b:
            a.extend([0] * (len_b - len_a))
        elif len_a > len_b:
            b.extend([0] * (len_a - len_b))
        return a, b

    try:
        version_str = importlib.metadata.version('pyrtlsdr')
    except importlib.metadata.PackageNotFoundError:
        return

    pyrtlsdr_version = parse_version(version_str)
    min_version = parse_version(PYRTLSDR_MIN_VERSION)
    normalize_version(pyrtlsdr_version, min_version)

    if pyrtlsdr_version[0] == -1:
        return
    if pyrtlsdr_version >= min_version:
        return

    def formatwarning(message, category, filename, lineno, line=None):
        return f'{filename}: {category.__name__}:\n{message}\n'

    orig_fmt = warnings.formatwarning
    try:
        warnings.formatwarning = formatwarning
        warnings.warn(
            f'pyrtlsdr>={PYRTLSDR_MIN_VERSION} required, '
            f'but version "{version_str}" is installed.\n'
            'To update, run: pip install --upgrade pyrtlsdr',
            category=VersionWarning,
        )
    finally:
        warnings.formatwarning = orig_fmt

check_pyrtlsdr_version()
