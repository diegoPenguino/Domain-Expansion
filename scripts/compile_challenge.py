"""Turn a challenge bot's source into a file that runs but does not show the source.

The source of a challenge bot stays out of this public repo. This script compiles it to
Python 3.13 bytecode, without docstrings or comments, and writes challenge/<name>.py: a
small loader that runs that bytecode. The bot plays exactly the same, and the page has
nothing readable to show.

It is not encryption: anyone determined can disassemble bytecode with the dis module. It
only keeps the strategy from being read at a glance.

Usage: python scripts/compile_challenge.py path/to/bot.py
"""

import base64
import marshal
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "challenge"

TEMPLATE = '''\
# Bot del reto de Domain Expansion: "{name}".
# Su código es secreto: esto es su bytecode de Python 3.13, no el código fuente.
# Generado con scripts/compile_challenge.py; no lo edites a mano.
import sys as _sys

if _sys.version_info[:2] != (3, 13):
    raise RuntimeError("Este bot necesita Python 3.13")

import base64 as _base64
import marshal as _marshal

exec(_marshal.loads(_base64.b64decode("""
{payload}
""")))
'''


def main() -> None:
    if sys.version_info[:2] != (3, 13):
        sys.exit("Run this with Python 3.13, the version Pyodide uses on the page.")
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    source_path = Path(sys.argv[1])
    name = source_path.stem
    # optimize=2 drops docstrings; the filename hides where the source lives.
    code = compile(source_path.read_text(encoding="utf-8"), f"<{name}>", "exec", optimize=2)
    payload = "\n".join(textwrap.wrap(base64.b64encode(marshal.dumps(code)).decode(), 76))

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"{name}.py"
    out.write_text(TEMPLATE.format(name=name, payload=payload), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
