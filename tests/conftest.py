import os
import sys

# The platform runs `uvicorn src.main:g.app` from the repo root, so modules import each other as `src.*`.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.dirname(os.path.abspath(__file__))
for path in (ROOT, TESTS):
    if path not in sys.path:
        sys.path.insert(0, path)
