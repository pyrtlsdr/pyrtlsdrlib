import sys
import platform

from . import BuildType

def get_os_type() -> BuildType:
    uname = platform.uname()
    if uname.system == 'Linux':
        if 'ubuntu' in uname.version.lower():
            t = BuildType.ubuntu
            t |= uname.machine
            return t
    elif uname.system == 'Darwin':
        t = BuildType.macos
        t |= uname.machine
        return t
    elif uname.system == 'Windows':
        t = BuildType.windows
        is_64bit = sys.maxsize > 2**32
        if is_64bit:
            t |= BuildType.w64
        else:
            t |= BuildType.w32
        return t
    return BuildType.unknown
