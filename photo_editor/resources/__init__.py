"""Bundled resources (window icon)."""
import os
import sys


def resource_path(name):
    """Path of a bundled file, both from source and inside a PyInstaller / py2app bundle."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        for sub in ("photo_editor/resources", "resources", ""):
            p = os.path.join(base, sub, name)
            if os.path.exists(p):
                return p
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
