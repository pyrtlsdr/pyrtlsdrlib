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

def test_no_platform_free_wheels_exist():
    pkg_dirs = [Path(name) for name in ['dist', 'wheelhouse'] if Path(name).exists()]
    assert len(pkg_dirs)
    for pkg_dir in pkg_dirs:
        l = [f for f in pkg_dir.glob('*-none-any.whl')]
        assert not len(l)
