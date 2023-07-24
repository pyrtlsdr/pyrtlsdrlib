import os
import sys
import platform
from setuptools import setup, find_namespace_packages

MACOSX_VERSIONS = '.'.join([
    'macosx_10_6_x86_64',  # for compatibility with pip < v21
    'macosx_10_6_universal2',
])

IS_CIBUILDWHEEL = os.environ.get('PYRTLSDRLIB_CIBUILDWHEEL') == 'true'

def get_os_type():
    if 'PYRTLSDRLIB_PLATFORM' in os.environ:
        return os.environ['PYRTLSDRLIB_PLATFORM']
    return 'any'

def get_architecture():
    if 'PYRTLSDRLIB_ARCHITECTURE' in os.environ:
        return os.environ['PYRTLSDRLIB_ARCHITECTURE']
    return platform.machine()

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
ARCH = get_architecture()

if 'linux' in OS_TYPE:
    LIB_GLOB = 'librtlsdr.so*'
    PLAT_MODULES = ['ubuntu_x86_x64']
elif OS_TYPE == 'macos':
    LIB_GLOB = '*.dylib'
    PLAT_MODULES = ['macos_arm64', 'macos_x86_x64']
elif OS_TYPE == 'win32':
    LIB_GLOB = 'librtlsdr_w32*.dll'
    PLAT_MODULES = ['windows_w32_static']
elif OS_TYPE == 'win64':
    LIB_GLOB = 'librtlsdr_w64*.dll'
    PLAT_MODULES = ['windows_w64_static']
else:
    LIB_GLOB = 'librtlsdr*'
    PLAT_MODULES = []

pkg_data = {
    '*':['LICENSE*', 'README*'],
    'pyrtlsdrlib.lib':['*.json', LIB_GLOB],
    'pyrtlsdrlib.lib.custom_build':['*.json', LIB_GLOB],
}
pkg_data.update({f'pyrtlsdrlib.lib.{m}':['*.json', LIB_GLOB] for m in PLAT_MODULES})

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    # cmdclass = {}
    raise
else:
    class bdist_wheel_half_pure(bdist_wheel):
        """Create OS-dependent, but Python-independent wheels."""

        def initialize_options(self):
            super().initialize_options()
            self.root_is_pure = False
            self.universal = False

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
