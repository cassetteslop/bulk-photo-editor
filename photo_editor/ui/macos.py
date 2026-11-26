"""macOS integration. Every function is a safe no-op on other platforms / without pyobjc."""
import sys

IS_MAC = sys.platform == "darwin"


def force_dark_appearance():
    """Ask AppKit for the Dark Aqua appearance so native widgets are dark whatever the system setting.
    Needs pyobjc (`pip install pyobjc-framework-Cocoa`); returns True if applied."""
    if not IS_MAC:
        return False
    try:
        from AppKit import NSApplication, NSAppearance
        NSApplication.sharedApplication().setAppearance_(
            NSAppearance.appearanceNamed_("NSAppearanceNameDarkAqua"))
        return True
    except Exception:
        return False


def set_process_name(name):
    """Show `name` instead of "Python" in the menu bar when running from source."""
    if not IS_MAC:
        return
    try:
        from Foundation import NSBundle
        info = NSBundle.mainBundle().infoDictionary()
        info["CFBundleName"] = name
    except Exception:
        pass


def register_events(root, on_open_paths):
    """Hook Finder / Dock events: files or folders dropped on the icon, `open -a`, the Quick Action,
    and clicking the Dock icon again."""
    if not IS_MAC:
        return
    try:
        root.createcommand("::tk::mac::OpenDocument", lambda *paths: on_open_paths(list(paths)))
        root.createcommand("::tk::mac::ReopenApplication", lambda *a: (root.deiconify(), root.lift()))
    except Exception:
        pass
