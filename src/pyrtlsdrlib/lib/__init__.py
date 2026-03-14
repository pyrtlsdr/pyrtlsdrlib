from typing import cast
import sys
from ctypes import CDLL
import traceback
from pathlib import Path

if sys.version_info < (3, 9):
    import importlib_resources
else:
    import importlib.resources as importlib_resources


def resource_filename(mod_name: str, filename: str) -> Path:
    return Path(str(importlib_resources.files(mod_name) / filename))


from pyrtlsdrlib import BuildType
from pyrtlsdrlib.platform import get_os_type
from . import custom_build

BUILD_TYPE_LIB_GLOBS = {
    BuildType.macos: '*.dylib',
    BuildType.linux: 'librtlsdr.so*',
    BuildType.windows | BuildType.w32: 'librtlsdr_w32*.dll',
    BuildType.windows | BuildType.w64: 'librtlsdr_w64*.dll',
}

def iter_library_files():
    os_type = get_os_type()
    lib_glob = BUILD_TYPE_LIB_GLOBS.get(os_type)
    if BuildType.linux in os_type:
        lib_glob = BUILD_TYPE_LIB_GLOBS[BuildType.linux]
    if lib_glob is not None:
        for lib_pkg in (custom_build.__name__, __name__):
            lib_dir = Path(resource_filename(lib_pkg, ''))
            yield from lib_dir.glob(lib_glob)


def get_library_files():
    return [p for p in iter_library_files()]


def load_librtlsdr():
    for lib_file in iter_library_files():
        try:
            dll = CDLL(str(lib_file))
        except Exception as exc:
            print(f'Could not load {lib_file}. Exception: {exc!r}')
            dll = None
        if dll is not None:
            return dll
