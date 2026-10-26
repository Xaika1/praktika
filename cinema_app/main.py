import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
