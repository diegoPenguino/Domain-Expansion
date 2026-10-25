"""Assemble the static site in _site/: the web page, the engine and the bots.

Run from anywhere: python scripts/build_site.py
Then preview with: python -m http.server -d _site 8000
"""

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"

# Bots in codes/ that stay out of the web page: templates and examples, not participants.
HIDDEN_BOTS = {"player1", "player2", "player3"}

# Files whose URLs carry the version, and the placeholder they use.
VERSIONED = ["index.html", "runner.html", "app.js", "runner.js"]
PLACEHOLDER = "__VERSION__"


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "web", OUT)
    shutil.copy2(ROOT / "simulator.py", OUT / "simulator.py")

    bots_out = OUT / "codes"
    bots_out.mkdir()
    names = []
    for path in sorted((ROOT / "codes").glob("*.py"), key=lambda p: p.stem.lower()):
        if path.stem == "__init__" or path.stem in HIDDEN_BOTS:
            continue
        shutil.copy2(path, bots_out / path.name)
        names.append(path.stem)

    # Challenge bots: only their compiled loader is public (scripts/compile_challenge.py).
    challenge_out = OUT / "challenge"
    challenge_out.mkdir()
    challenge = []
    for path in sorted((ROOT / "challenge").glob("*.py")):
        shutil.copy2(path, challenge_out / path.name)
        challenge.append(path.stem)

    manifest = {"bots": names, "challenge": challenge}
    (OUT / "bots.json").write_text(json.dumps(manifest, indent=2) + "\n")

    version = site_hash()
    for name in VERSIONED:
        path = OUT / name
        path.write_text(path.read_text(encoding="utf-8").replace(PLACEHOLDER, version), encoding="utf-8")
    print(f"Built {OUT.relative_to(ROOT)}/ with {len(names)} bots, {len(challenge)} challenge, version {version}")


def site_hash() -> str:
    """Short hash of every file in the built site, so any change gives new URLs."""
    digest = hashlib.sha256()
    for path in sorted(p for p in OUT.rglob("*") if p.is_file()):
        digest.update(path.relative_to(OUT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


if __name__ == "__main__":
    main()
