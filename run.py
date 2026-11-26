#!/usr/bin/env python3
"""Launcher (also the py2app entry point):  python run.py [photos or folders ...]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from photo_editor.app import main  # noqa: E402

if __name__ == "__main__":
    main()
