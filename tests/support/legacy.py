"""`b` = one namespace with every public/private name of the package, so tests read like the
original single-file app (b.detect_product, b.App, ...). Import `faketk` first for headless runs."""
import importlib
import pkgutil
import types

import photo_editor

b = types.SimpleNamespace()
for _m in pkgutil.walk_packages(photo_editor.__path__, "photo_editor."):
    if _m.name.endswith("__main__"):
        continue
    mod = importlib.import_module(_m.name)
    for k, v in vars(mod).items():
        if not k.startswith("__"):
            setattr(b, k, v)
