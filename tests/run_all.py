"""Run every test script:  python tests/run_all.py"""
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
failed = []
for name in ("test_watermark", "test_detect", "test_detect_dark", "test_crop", "test_open_paths_theme", "test_dnd", "test_gui"):
    print(f"=== {name}")
    r = subprocess.run([sys.executable, os.path.join(here, name + ".py")])
    if r.returncode:
        failed.append(name)
print("\nALL PASSED" if not failed else f"\nFAILED: {failed}")
sys.exit(1 if failed else 0)
