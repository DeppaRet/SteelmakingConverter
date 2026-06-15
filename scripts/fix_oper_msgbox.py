"""Replace QMessageBox blocks in OperForm with i18n helpers."""
import re
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "OperForm.py"
text = path.read_text(encoding="utf-8")

# Add helper after class start if missing
if "_show_critical" not in text:
    text = text.replace(
        "class Ui_OperatorForm(object):",
        "class Ui_OperatorForm(object):\n\n"
        "    def _show_critical(self, info, title=\"Ошибка\", text=\"Внимание\"):\n"
        "        msg_critical(getattr(self, '_oper_form', None), title, text, info)\n\n"
        "    def _show_warning(self, info, title=\"Внимание\", text=\"Внимание\"):\n"
        "        msg_warning(getattr(self, '_oper_form', None), title, text, info)\n",
    )

pattern = re.compile(
    r"(\s*)msg = QMessageBox\(\)\s*\n"
    r"\1msg\.setIcon\(QMessageBox\.Critical\)\s*\n"
    r"\1msg\.setWindowTitle\(\"([^\"]+)\"\)\s*\n"
    r"\1msg\.setText\(\"([^\"]+)\"\)\s*\n"
    r"\1msg\.setInformativeText\(([^\n]+)\)\s*\n"
    r"(?:\1(?:# [^\n]*\n)?)?"
    r"(?:\1app_theme\.style_message_box\(msg\)\s*\n)?"
    r"\1msg\.exec_\(\)",
    re.MULTILINE,
)

def repl(m):
    indent, title, main, info = m.group(1), m.group(2), m.group(3), m.group(4)
    return f'{indent}self._show_critical({info}, "{title}", "{main}")'

new_text, n = pattern.subn(repl, text)
print(f"Replaced {n} critical blocks")

# QMessageBox.warning/critical one-liners
warn_pat = re.compile(
    r"QMessageBox\.warning\(\s*([^,]+),\s*\"([^\"]+)\",\s*\"([^\"]+)\"\s*\)"
)
new_text, n2 = warn_pat.subn(
    r'msg_warning(\1, "\2", "\3")', new_text
)
print(f"Replaced {n2} warning one-liners")

crit_pat = re.compile(
    r"QMessageBox\.critical\(\s*([^,]+),\s*\"([^\"]+)\",\s*([^)]+)\)"
)
new_text, n3 = crit_pat.subn(
    r'msg_critical(\1, "\2", \3)', new_text
)
print(f"Replaced {n3} critical one-liners")

path.write_text(new_text, encoding="utf-8")
