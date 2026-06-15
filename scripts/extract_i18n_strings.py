"""Extract Russian UI strings from Python sources."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
strings: set[str] = set()

patterns = [
    re.compile(r'_t(?:ranslate)?\([^,]+,\s*["\']([^"\']+)["\']'),
    re.compile(r'tr\([^,]+,\s*["\']([^"\']+)["\']'),
    re.compile(r'setToolTip\(["\']([^"\']+)["\']'),
    re.compile(r'setWindowTitle\(["\']([^"\']+)["\']'),
    re.compile(r'setText\(["\']([^"\']+)["\']'),
    re.compile(r'QLabel\(["\']([^"\']+)["\']'),
    re.compile(r'QGroupBox\(["\']([^"\']+)["\']'),
    re.compile(r'setPlaceholderText\(["\']([^"\']+)["\']'),
    re.compile(r'setTitle\(["\']([^"\']+)["\']'),
]

def has_cyrillic(s: str) -> bool:
    return any("\u0400" <= c <= "\u04FF" or c in "Ёё" for c in s)

for p in ROOT.rglob("*.py"):
    if "i18n" in p.parts or ".idea" in p.parts or "scripts" in p.parts:
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        continue
    for pat in patterns:
        for m in pat.finditer(text):
            s = m.group(1).strip()
            if s and has_cyrillic(s):
                strings.add(s)

out = ROOT / "i18n" / "translations_en.json"
existing = {}
if out.is_file():
    existing = json.loads(out.read_text(encoding="utf-8"))

merged = {k: existing.get(k, k) for k in sorted(strings)}
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {len(merged)} keys to {out}")
