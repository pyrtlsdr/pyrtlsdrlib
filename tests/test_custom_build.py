from pathlib import Path
import pytest

from pyrtlsdrlib.lib import get_library_files, load_librtlsdr

from conftest import HAS_CUSTOM_BUILD, IS_CI, MACOS_ARCH

pytestmark = pytest.mark.skipif(not HAS_CUSTOM_BUILD, reason='No custom build')

def test_custom_build_exists(custom_lib_root):
    lib_files = []
    for p in get_library_files():
        if p.parent != custom_lib_root:
            continue
        lib_files.append(p)
    assert len(lib_files) > 0

@pytest.mark.skipif(IS_CI and MACOS_ARCH=='arm64')
def test_custom_build_loads(custom_lib_root):
    dll = load_librtlsdr()
    assert dll is not None
    dll_file = Path(dll._name)
    assert dll_file.parent == custom_lib_root
