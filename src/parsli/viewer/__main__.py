from .core import Viewer


def main():
    app = Viewer()
    app.server.start()


if __name__ == "__main__":
    main()
