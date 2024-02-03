#!/bin/bash

set -e -u -x

uname -a
ls -al /opt/python
echo "python path: $PY_PATH"
$PY_PATH -V
$PY_PATH -c "import distutils;print(distutils.util.get_platform())"

echo "Installing libusb"
$PKG_MGR install -y libusbx-devel

echo "Removing existing library files"
rm /io/src/pyrtlsdrlib/lib/*.dll
rm /io/src/pyrtlsdrlib/lib/*.dylib
rm /io/src/pyrtlsdrlib/lib/librtlsdr.so*

echo "Installing pip dependencies"
$PY_PATH -m pip install pygithub requests loguru build json-object-factory click pytest
$PY_PATH -m pip install -e /io

echo "Building librtlsdr"
$PY_PATH /io/tools/get_releases.py --build-types source

echo "Testing build"
$PY_PATH -m pytest /io/tests/test_custom_build.py

echo "Building wheel"
$PY_PATH -m build -w /io --outdir /io/dist

echo "Repairing wheels"
ls -al /io/dist
for whl in /io/dist/*.whl; do
    auditwheel show "$whl"
    auditwheel repair "$whl" --wheel-dir /io/wheelhouse
done
ls -al /io/wheelhouse
