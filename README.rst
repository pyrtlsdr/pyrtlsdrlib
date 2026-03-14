pyrtlsdrlib
===========

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
