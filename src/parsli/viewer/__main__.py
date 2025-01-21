from __future__ import annotations

from .core import Viewer


def main():
    app = Viewer()
    app.server.start()


if __name__ == "__main__":
    main()
