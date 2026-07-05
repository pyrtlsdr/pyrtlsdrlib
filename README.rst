pyrtlsdrlib
===========

|uv badge| |actions badge| |PyPI version| |PyPI license| |PyPI pyversions| |PyPI download month|


.. |uv badge| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
    :alt: uv
    :target: https://docs.astral.sh/uv/

.. |actions badge| image:: https://img.shields.io/github/actions/workflow/status/pyrtlsdr/pyrtlsdrlib/build-lib.yml
    :alt: GitHub Actions Workflow Status
    :target: https://github.com/pyrtlsdr/pyrtlsdrlib/actions

.. |PyPI version| image:: https://img.shields.io/pypi/v/pyrtlsdrlib.svg
    :alt: PyPI version
    :target: https://pypi.python.org/pypi/pyrtlsdrlib/

.. |PyPI license| image:: https://img.shields.io/pypi/l/pyrtlsdrlib.svg
    :alt: PyPI license
    :target: https://pypi.python.org/pypi/pyrtlsdrlib/

.. |PyPI pyversions| image:: https://img.shields.io/pypi/pyversions/pyrtlsdrlib.svg
    :alt: PyPI Python versions
    :target: https://pypi.python.org/pypi/pyrtlsdrlib/

.. |PyPI download month| image:: https://img.shields.io/pypi/dm/pyrtlsdrlib.svg
    :alt: PyPI download month
    :target: https://pypi.python.org/pypi/pyrtlsdrlib/



Description
-----------

A helper for `pyrtlsdr`_ that includes pre-built binaries of `librtlsdr`_
(which pyrtlsdr depends on).

Contains libraries built for the following systems:

- Ubuntu Linux (x86_64 and aarch64)
- Mac OSX (Intel)
- Mac OSX (M1 / arm64)
- Windows (32 and 64 bit)


Installation
------------

Install directly with ``pip``

.. code:: bash

    pip install pyrtlsdrlib


Or as an "extra" dependency of pyrtlsdr

.. code:: bash

    pip install pyrtlsdr[lib]



.. _librtlsdr: https://github.com/librtlsdr/librtlsdr
.. _pyrtlsdr: https://github.com/pyrtlsdr/pyrtlsdr
