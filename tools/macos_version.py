import argparse
import distutils.util

VERSION_NAMES = {
    '11': 'big_sur',
    '12': 'monterey',
    '13': 'ventura',
    '14': 'sonoma',
}

def get_named_version(version: str) -> str:
    key = version.split('.')[0]
    return VERSION_NAMES[key]

def get_current_version_name() -> str:
    version = distutils.util.get_macosx_target_ver()
    return get_named_version(version)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--force-version', dest='force_version')
    args = p.parse_args()
    if args.force_version is not None:
        if '-' in args.force_version:
            version = None
            for v in args.force_version.split('-'):
                if v.isdigit():
                    version = v
                    break
            if version is None:
                raise ValueError(f'Could not parse version from "{args.force_version}"')
        else:
            version = args.force_version
        print(get_named_version(version))
    else:
        print(get_current_version_name())
