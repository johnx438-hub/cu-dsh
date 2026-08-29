"""PyInstaller entry for cu-dsh.exe (see cu-dsh.spec)."""
import sys

from cu_dsh.cli import main

if __name__ == "__main__":
    sys.exit(main())
