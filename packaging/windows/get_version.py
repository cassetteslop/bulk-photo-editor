import re
import os
print(re.search(r'__version__ = "([^"]+)"', open(os.path.join(os.path.dirname(__file__), "..", "..", "photo_editor", "__init__.py")).read()).group(1))
