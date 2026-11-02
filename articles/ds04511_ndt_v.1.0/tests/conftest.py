import sys
from pathlib import Path

ARTICLE_DIR = Path(__file__).resolve().parents[1]
SRC = ARTICLE_DIR / "src"
REPO_ROOT = ARTICLE_DIR.parents[1]
NMD_ANALYSIS_ROOT = REPO_ROOT / "nmd-analysis"

for path in (SRC, NMD_ANALYSIS_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)
