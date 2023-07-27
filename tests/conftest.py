import os
from pathlib import Path
import pytest
import platform

from pyrtlsdrlib import lib as LIB_MODULE
from pyrtlsdrlib.lib import custom_build as CUSTOM_LIB_MODULE
from pyrtlsdrlib.lib import resource_filename

HAS_CUSTOM_BUILD = os.environ.get('PYRTLSDRLIB_NO_CUSTOM') not in ['1', 'true']
IS_CI = os.environ.get('CI') == 'true'
MACOS_ARCH = os.environ.get('MACOS_ARCH')


@pytest.fixture
def package_lib_root():
    return Path(resource_filename(LIB_MODULE.__name__, ''))


@pytest.fixture
def custom_lib_root():
    return Path(resource_filename(CUSTOM_LIB_MODULE.__name__, ''))
