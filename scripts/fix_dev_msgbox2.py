"""Replace remaining QMessageBox blocks in DeveloperForm."""
import re
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "DeveloperForm.py"
text = path.read_text(encoding="utf-8")

pattern = re.compile(
    r"(\s*)msg = QMessageBox\(\)\s*\n"
    r"\1msg\.setIcon\(QMessageBox\.Critical\)\s*\n"
    r"\1msg\.setWindowTitle\(\"([^\"]+)\"\)\s*\n"
    r"\1msg\.setText\(\"([^\"]+)\"\)\s*\n"
    r"\1msg\.setInformativeText\(([^\n]+)\)\s*\n"
    r"(?:\1#[^\n]*\n)*"
    r"\1msg\.exec_\(\)",
    re.MULTILINE,
)

def repl(m):
    indent, title, main, info = m.group(1), m.group(2), m.group(3), m.group(4)
    return f'{indent}self._show_critical({info}, "{title}", "{main}")'

new_text, n = pattern.subn(repl, text)
print(f"Replaced {n}")
path.write_text(new_text, encoding="utf-8")
