#! /usr/bin/env python3
import os
import subprocess
import shlex
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = PROJECT_ROOT / 'build'
PLATFORMS = ['macos', 'win32', 'win64']

def main():
    def build_wheel(os_type):
        env = os.environ.copy()
        if os_type != 'any':
            env['PYRTLSDRLIB_PLATFORM'] = os_type
        cmd_str = 'python -m build -w'
        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)
        subprocess.run(shlex.split(cmd_str), env=env, check=True)
    for os_type in PLATFORMS:
        build_wheel(os_type)

if __name__ == '__main__':
    main()
