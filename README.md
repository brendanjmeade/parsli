# parsli

[![Actions Status][actions-badge]][actions-link]
[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link] ![PyPI download][download-badge]

<!-- SPHINX-START -->

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/brendanjmeade/parsli/workflows/Test%20and%20Release/badge.svg
[actions-link]:             https://github.com/brendanjmeade/parsli/actions
[pypi-link]:                https://pypi.org/project/parsli/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/parsli
[pypi-version]:             https://img.shields.io/pypi/v/parsli
[rtd-badge]:                https://readthedocs.org/projects/parsli/badge/?version=latest
[rtd-link]:                 https://parsli.readthedocs.io/en/latest/?badge=latest
[download-badge]:           https://img.shields.io/pypi/dm/parsli

<!-- prettier-ignore-end -->

## Introduction

Parsli is a VTK+trame based viewer for fault system kinematics that enables fast
exploration and export of time animation.

## Getting started

First you should setup a virtual environment for this Python Application. You
can use conda, uv or anything else for managing your Python runtime. For the
following commands, we will be using `uv` with Python 3.10.

```
uv venv -p 3.10
source .venv/bin/activate
uv pip install parsli
```

Once your environment is loaded, you can start the viewer by running the
following command:

```
# use remote rendering
python -m parsli.viewer --data ./data/model_0000000881_multi.hdf5

# use wasm for local rendering
python -m parsli.viewer --data ./data/model_0000000881_multi.hdf5 --wasm

# use shorthand executable
parsli --data ./data/model_0000000881_multi.hdf5
```

![App](https://raw.githubusercontent.com/brendanjmeade/parsli/refs/heads/main/parsli.png)

**Keyboard binding**

- **left/right/up/down arrow**: Rotate camera by 1°. Modifier x5 `<alt>`.
- **-/+**: Zoom out / Zoom in.
- **r**: Reset camera to data
- **t**: Snap view up to true vertical.
- **f**: Focus to the mesh bounds
- **home**: Go to first timestep
- **end**: Go to last timestep
- **space**: Toggle play/stop animation
- **</>**: Previous/Next timestep. Modifiers x10 `alt` or `shift`, x100
  `alt`+`shift`.

Once you've exported a couple of time animations, you can play them back using
the player. Just add all the paths you want to see after the `--data` argument.

```
parsli-player --data ./export/dip_slip ./export/strike_slip ./export/dip_slip_formula ./export/strike_slip_formula
```

![Player](https://raw.githubusercontent.com/brendanjmeade/parsli/refs/heads/main/parsli-player.png)

**Keyboard binding**

- **right arrow**: Go to next timestep
- **left arrow**: Go to previous timestep
- **home**: Go to first timestep
- **end**: Go to last timestep
- **space**: Toggle play/stop animation

## Development setup

We assume your virtual environment is activated

```
uv pip install -e ".[dev]"
pre-commit install
```

This will automatically format and some static checking on the code at commit
time, but you can also run it by hand using the following command line.

```
pre-commit run --all-files
```

Nox can also be used for running tests or linting the code.

```
# run everything
nox

# run just the linting
nox -s lint
```

## Commit message convention

Semantic release rely on
[conventional commits](https://www.conventionalcommits.org/) to generate new
releases and changelog.
