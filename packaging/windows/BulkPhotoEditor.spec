# PyInstaller spec - build with:  pyinstaller --noconfirm --clean packaging/windows/BulkPhotoEditor.spec
# (packaging/windows/build_windows.bat does this for you.)  Produces dist\BulkPhotoEditor\BulkPhotoEditor.exe
import os
import re

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
init = open(os.path.join(ROOT, "photo_editor", "__init__.py"), encoding="utf-8").read()
NAME = re.search(r'APP_NAME = "([^"]+)"', init).group(1)

datas = collect_data_files("photo_editor")                 # icon.png
hiddenimports = collect_submodules("photo_editor")
try:                                                        # drag-and-drop (tkdnd native library lives in the package data)
    datas += collect_data_files("tkinterdnd2")
    hiddenimports += ["tkinterdnd2"]
except Exception:
    pass

a = Analysis(
    [os.path.join(ROOT, "run.py")],
    pathex=[ROOT],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["matplotlib", "scipy", "pandas", "IPython", "pytest", "PyQt5", "PyQt6", "PySide2", "PySide6"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="BulkPhotoEditor",
    console=False,                                          # no black console window
    icon=os.path.join(SPECPATH, "BulkPhotoEditor.ico"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="BulkPhotoEditor")
