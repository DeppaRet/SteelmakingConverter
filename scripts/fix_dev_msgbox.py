"""Replace QMessageBox in DeveloperForm with i18n helpers."""
import re
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "DeveloperForm.py"
text = path.read_text(encoding="utf-8")

if "from i18n import msg_critical" not in text:
    text = text.replace(
        "from i18n import tr",
        "from i18n import tr, msg_critical\nfrom view_toggles import ViewTogglesBar\n"
        "from locale_settings import manager as locale_manager",
    )

if "_show_critical" not in text:
    text = text.replace(
        "class Ui_Form(object):",
        "class Ui_Form(object):\n\n"
        "    def _show_critical(self, info, title=\"Ошибка\", text=\"Внимание\"):\n"
        "        msg_critical(getattr(self, '_dev_form', None), title, text, info)\n",
    )

pattern = re.compile(
    r"(\s*)msg = QMessageBox\(\)\s*\n"
    r"\1msg\.setIcon\(QMessageBox\.Critical\)\s*\n"
    r"\1msg\.setWindowTitle\(\"([^\"]+)\"\)\s*\n"
    r"\1msg\.setText\(\"([^\"]+)\"\)\s*\n"
    r"\1msg\.setInformativeText\(([^\n]+)\)\s*\n"
    r"\1msg\.exec_\(\)",
    re.MULTILINE,
)

def repl(m):
    indent, title, main, info = m.group(1), m.group(2), m.group(3), m.group(4)
    return f'{indent}self._show_critical({info}, "{title}", "{main}")'

new_text, n = pattern.subn(repl, text)
print(f"DeveloperForm: {n} replacements")
path.write_text(new_text, encoding="utf-8")
