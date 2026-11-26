"""Windows integration (no-ops elsewhere): crisp text on high-DPI screens and a proper taskbar identity."""
import sys

IS_WINDOWS = sys.platform.startswith("win")


def enable_high_dpi():
    """Call BEFORE the Tk root is created, otherwise Windows bitmap-scales the whole window."""
    if not IS_WINDOWS:
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)      # per-monitor
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def set_app_user_model_id(app_id):
    """Group the taskbar button under our own icon instead of python.exe's."""
    if not IS_WINDOWS:
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass
