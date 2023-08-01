from pathlib import Path

def test_no_platform_free_wheels_exist():
    pkg_dirs = [Path(name) for name in ['dist', 'wheelhouse'] if Path(name).exists()]
    assert len(pkg_dirs)
    for pkg_dir in pkg_dirs:
        l = [f for f in pkg_dir.glob('*-none-any.whl')]
        assert not len(l)
