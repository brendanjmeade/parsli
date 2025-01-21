from __future__ import annotations

import importlib.metadata

import parsli as m


def test_version():
    assert importlib.metadata.version("parsli") == m.__version__
