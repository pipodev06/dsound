# Punto de entrada del ejecutable (PyInstaller). Equivale a `python -m dsound`.
import sys

from dsound.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
