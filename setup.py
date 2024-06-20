import os
import sys
import platform
import distutils.util
from setuptools import setup, find_namespace_packages

MACOSX_VERSIONS = {
    None:'macosx',
    'x86_64':'macosx_10_6_x86_64',
    'arm64':'macosx_10_6_arm64'
}

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

def get_os_arch():
    return os.environ.get('PYRTLSDRLIB_ARCH', platform.machine())

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
    'pyrtlsdrlib.lib.custom_build':['*.json', LIB_GLOB],
}

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    cmdclass = {}
else:
    class bdist_wheel_half_pure(bdist_wheel):
        """Create OS-dependent, but Python-independent wheels."""

        def get_tag(self):
            oses = None
            if OS_TYPE == 'macos':
                arch = get_os_arch()
                os_ver = distutils.util.get_macosx_target_ver().split('.')[0]
                oses = f'macosx_{os_ver}_0_{arch}'
            elif OS_TYPE.lower().startswith('win'):
                arch = get_os_arch()
                if arch is not None:
                    if '32' in arch:
                        oses = 'win32'
                    elif '64' in arch:
                        oses = 'win_amd64'
                    else:
                        raise ValueError(f'Invalid value "{arch}" for "PYRTLSDRLIB_ARCH"')
                elif OS_TYPE == 'win32':
                    oses = 'win32'
                elif OS_TYPE == 'win64':
                    oses = 'win_amd64'
            elif OS_TYPE == 'linux':
                arch = get_os_arch()
                oses = f'linux_{arch}'
            if oses is None:
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
