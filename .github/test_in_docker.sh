#!/bin/bash

set -e -u -x
echo "foo"

PY_ABI="${PY_VERSION//.}"
PY_PATH="/opt/python/cp$PY_ABI-cp$PY_ABI/bin/python"
echo "PY_ABI=$PY_ABI"
echo "PY_PATH=$PY_PATH"
$PY_PATH -V
$PY_PATH -c "import distutils;print(distutils.util.get_platform())"


echo "Installing pyrtlsdrlib from wheel"
$PY_PATH -m pip install --no-index --find-links /io/dist pyrtlsdrlib

echo "Installing pyrtlsdr"
$PY_PATH -m pip install -e /io/$PYRTLSDR

echo "Testing rtlsdr import"
$PY_PATH -c "import rtlsdr;"

echo "Success"
