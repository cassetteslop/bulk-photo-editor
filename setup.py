"""Build the macOS app:   python setup.py py2app        (see packaging/build_mac_app.sh)"""
import os
import re
import sys

from setuptools import setup

here = os.path.dirname(os.path.abspath(__file__))
init = open(os.path.join(here, "photo_editor", "__init__.py"), encoding="utf-8").read()
VERSION = re.search(r'__version__ = "([^"]+)"', init).group(1)
NAME = re.search(r'APP_NAME = "([^"]+)"', init).group(1)
BUNDLE_ID = re.search(r'BUNDLE_ID = "([^"]+)"', init).group(1)
ICON = os.path.join(here, "packaging", "BulkPhotoEditor.icns")

PLIST = {
    "CFBundleName": NAME,
    "CFBundleDisplayName": NAME,
    "CFBundleIdentifier": BUNDLE_ID,
    "CFBundleShortVersionString": VERSION,
    "CFBundleVersion": VERSION,
    "LSMinimumSystemVersion": "11.0",
    "NSHighResolutionCapable": True,
    "NSRequiresAquaSystemAppearance": False,       # allow Dark Mode
    "NSHumanReadableCopyright": "Originals are never modified.",
    "LSApplicationCategoryType": "public.app-category.photography",
    # Lets Finder offer the app for images and folders, and delivers them via ::tk::mac::OpenDocument
    "CFBundleDocumentTypes": [
        {"CFBundleTypeName": "Image", "CFBundleTypeRole": "Editor", "LSHandlerRank": "Alternate",
         "LSItemContentTypes": ["public.image"]},
        {"CFBundleTypeName": "Folder", "CFBundleTypeRole": "Viewer", "LSHandlerRank": "Alternate",
         "LSItemContentTypes": ["public.folder"]},
    ],
}

PACKAGES = ["photo_editor", "PIL", "numpy"]
try:                                     # drag-and-drop support (bundles the native tkdnd library)
    import tkinterdnd2  # noqa: F401
    PACKAGES.append("tkinterdnd2")
except ImportError:
    pass

OPTIONS = {
    "argv_emulation": False,                        # unreliable on current macOS; Apple events are used
    "packages": PACKAGES,
    "includes": ["tkinter", "AppKit", "Foundation"],
    "excludes": ["matplotlib", "scipy", "pandas", "IPython", "pytest"],
    "plist": PLIST,
}
if os.path.exists(ICON):
    OPTIONS["iconfile"] = ICON

if sys.platform != "darwin" and "py2app" in sys.argv:
    sys.exit("py2app builds must be run on a Mac.")

setup(
    name=NAME.replace(" ", ""),
    version=VERSION,
    app=["run.py"],
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
