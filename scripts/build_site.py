"""Assemble the static site in _site/: the web page, the engine and the bots.

Run from anywhere: python scripts/build_site.py
Then preview with: python -m http.server -d _site 8000
"""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "web", OUT)
    shutil.copy2(ROOT / "simulator.py", OUT / "simulator.py")

    bots_out = OUT / "codes"
    bots_out.mkdir()
    names = []
    for path in sorted((ROOT / "codes").glob("*.py"), key=lambda p: p.stem.lower()):
        if path.stem == "__init__":
            continue
        shutil.copy2(path, bots_out / path.name)
        names.append(path.stem)

    (OUT / "bots.json").write_text(json.dumps({"bots": names}, indent=2) + "\n")
    print(f"Built {OUT.relative_to(ROOT)}/ with {len(names)} bots")


if __name__ == "__main__":
    main()
