from ctypes import CDLL
from importlib import import_module
import traceback
from pkg_resources import resource_filename
from pathlib import Path

from pyrtlsdrlib import BuildType
from pyrtlsdrlib.platform import get_os_type, get_os_arch_dirname
from . import custom_build

BUILD_TYPE_LIB_GLOBS = {
    BuildType.macos: '*.dylib',
    BuildType.ubuntu: 'librtlsdr.so*',
    BuildType.windows | BuildType.w32: 'librtlsdr_w32*.dll',
    BuildType.windows | BuildType.w64: 'librtlsdr_w64*.dll',
}

def iter_library_files():
    build_type = get_os_type()
    os_filter = BuildType.all_os | BuildType.w32 | BuildType.w64
    os_type = build_type & os_filter
    lib_glob = BUILD_TYPE_LIB_GLOBS.get(os_type)
    if lib_glob is not None:
        lib_dir = get_os_arch_dirname(build_type)
        lib_dir = Path(resource_filename(__name__, lib_dir))
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
