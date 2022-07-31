import os
import sys
import platform
from setuptools import setup, find_namespace_packages

MACOSX_VERSIONS = '.'.join([
    'macosx_10_6_x86_64',  # for compatibility with pip < v21
    'macosx_10_6_universal2',
])

def get_os_type():
    if 'PYRTLSDRLIB_PLATFORM' in os.environ:
        return os.environ['PYRTLSDRLIB_PLATFORM']
    return 'any'

    # uname = platform.uname()
    # if uname.system == 'Linux':
    #     if 'ubuntu' in uname.version.lower():
    #         return 'ubuntu'
    # elif uname.system == 'Darwin':
    #     return 'macos'
    # elif uname.system == 'Windows':
    #     is_64bit = sys.maxsize > 2**32
    #     if is_64bit:
    #         return 'win64'
    #     else:
    #         return 'win32'
    # return 'unknown'

OS_TYPE = get_os_type()

if 'linux' in OS_TYPE:
    LIB_GLOB = 'librtlsdr.so*'
elif OS_TYPE == 'macos':
    LIB_GLOB = '*.dylib'
elif OS_TYPE == 'win32':
    LIB_GLOB = 'librtlsdr_w32*.dll'
elif OS_TYPE == 'win64':
    LIB_GLOB = 'librtlsdr_w64*.dll'
else:
    LIB_GLOB = 'librtlsdr*'

pkg_data = {
    '*':['LICENSE*', 'README*'],
    'pyrtlsdrlib.lib':['*.json', LIB_GLOB],
}

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    cmdclass = {}
else:
    class bdist_wheel_half_pure(bdist_wheel):
        """Create OS-dependent, but Python-independent wheels."""

        def get_tag(self):
            if OS_TYPE == 'macos':
                oses = MACOSX_VERSIONS
            elif OS_TYPE == 'win32':
                oses = 'win32'
            elif OS_TYPE == 'win64':
                oses = 'win_amd64'
            else:
                oses = 'any'
            return 'py3', 'none', oses

    cmdclass = {'bdist_wheel': bdist_wheel_half_pure}

setup(
    cmdclass=cmdclass,
    packages=find_namespace_packages(
        where='src',
    ),
    package_dir={"": "src"},
    package_data=pkg_data,
    include_package_data=True,
)
