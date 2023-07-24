from __future__ import annotations
import sys
import platform

from . import BuildType

__all__ = ('get_os_type', 'get_os_arch_dirname')

def get_os_type() -> BuildType:
    uname = platform.uname()
    if uname.system == 'Linux':
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

def get_os_arch_dirname(build_type: BuildType|None = None) -> str:
    local_os_type = get_os_type()
    if build_type is None:
        build_type = local_os_type
    os_type = build_type.filter_os()
    if not len(os_type):
        os_type = local_os_type.filter_os()
    assert len(os_type) == 1
    arch_type = build_type.filter_archs()
    if not len(arch_type):
        arch_type = local_os_type.filter_archs()
    assert len(arch_type) == 1
    dirname = f'{os_type.name}_{arch_type.name}'
    if os_type & BuildType.windows:
        opts = build_type.filter_options()
        opts_sort = {o.value:o.name for o in opts}
        opts_str = '_'.join([opts_sort[k] for k in sorted(opts_sort.keys())])
        dirname = f'{dirname}_{opts_str}'
    return dirname
