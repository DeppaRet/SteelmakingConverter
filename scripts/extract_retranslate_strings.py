"""Extract _t() strings from retranslateUi methods."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "i18n" / "translations_en.json"
pat = re.compile(r'_t\([^,]+,\s*["\']([^"\']+)["\']')
strings: set[str] = set()

for p in ROOT.glob("*.py"):
    text = p.read_text(encoding="utf-8")
    for m in pat.finditer(text):
        s = m.group(1)
        if any("\u0400" <= c <= "\u04FF" for c in s):
            strings.add(s)

existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {}
merged = {k: existing.get(k, k) for k in sorted(set(existing) | strings)}
OUT.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Total keys: {len(merged)} (+{len(strings)} from _t)")
