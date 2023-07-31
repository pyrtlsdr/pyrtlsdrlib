
import distutils.util

VERSION_NAMES = {
    '11': 'big_sur',
    '12': 'monterey',
    '13': 'ventura',
}

def get_named_version(version: str) -> str:
    key = version.split('.')[0]
    return VERSION_NAMES[key]

def get_current_version_name() -> str:
    version = distutils.util.get_macosx_target_ver()
    return get_named_version(version)

if __name__ == '__main__':
    print(get_current_version_name())
