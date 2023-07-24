from pyrtlsdrlib import load_librtlsdr, get_library_files

def test_lib_loader():
    lib_files = get_library_files()
    print(lib_files)
    assert len(lib_files)
    dll = load_librtlsdr()
    assert dll is not None
