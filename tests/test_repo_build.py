from pathlib import Path
import pytest

from pyrtlsdrlib.lib import get_library_files, load_librtlsdr

from conftest import HAS_CUSTOM_BUILD


def test_repo_build_exists(package_lib_root):
    lib_files = []
    for p in get_library_files():
        if p.parent != package_lib_root:
            continue
        lib_files.append(p)
    assert len(lib_files) > 0

@pytest.mark.skipif(HAS_CUSTOM_BUILD, reason='Custom build exists')
def test_repo_build_loads(package_lib_root):
    dll = load_librtlsdr()
    assert dll is not None
    dll_file = Path(dll._name)
    assert dll_file.parent == package_lib_root
