"""Command-line entry point."""
import sys


def main(argv=None):
    from photo_editor import BUNDLE_ID
    from photo_editor.ui import platform_win
    platform_win.enable_high_dpi()                  # must happen before the Tk root exists
    platform_win.set_app_user_model_id(BUNDLE_ID)
    from photo_editor.ui.app import App, PlainApp
    args = [a for a in (sys.argv[1:] if argv is None else argv) if not a.startswith("-")]  # drop -psn_… etc.
    try:
        app = App(initial_paths=args)
    except Exception:
        # tkinterdnd2 is installed but its native library would not load: run without drag-and-drop
        app = PlainApp(initial_paths=args)
    app.mainloop()
