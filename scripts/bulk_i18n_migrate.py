"""Bulk i18n migrations for large form modules."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def migrate_retranslate(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "_translate = QtCore.QCoreApplication.translate",
        "from i18n import tr as _translate",
    )
    text = text.replace(
        "_t = QtCore.QCoreApplication.translate",
        "from i18n import tr as _t",
    )
    path.write_text(text, encoding="utf-8")
    print(f"retranslate: {path.name}")


def migrate_oper_msgbox(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "from i18n import msg_critical" not in text:
        text = text.replace(
            "from theme_toggle import ThemeToggle",
            "from theme_toggle import ThemeToggle\nfrom view_toggles import ViewTogglesBar\n"
            "from locale_settings import manager as locale_manager, get_language\n"
            "from i18n import msg_critical, msg_warning, tr",
        )
    # Standard critical block with optional style_message_box
    pattern = re.compile(
        r"(\s*)msg = QMessageBox\(\)\n"
        r"\1msg\.setIcon\(QMessageBox\.Critical\)\n"
        r"\1msg\.setWindowTitle\(\"([^\"]+)\"\)\n"
        r"\1msg\.setText\(\"([^\"]+)\"\)\n"
        r"(?:\1msg\.setInformativeText\(([^\n]+)\)\n)?"
        r"(?:\1app_theme\.style_message_box\(msg\)\n)?"
        r"\1msg\.exec_\(\)",
        re.MULTILINE,
    )

    def repl(m):
        indent = m.group(1)
        title = m.group(2)
        main = m.group(3)
        info = m.group(4) or '""'
        return (
            f"{indent}msg_critical(\n"
            f"{indent}    getattr(self, '_oper_form', None),\n"
            f"{indent}    \"{title}\", \"{main}\", {info},\n"
            f"{indent})"
        )

    new_text, n = pattern.subn(repl, text)
    path.write_text(new_text, encoding="utf-8")
    print(f"msgbox replacements in {path.name}: {n}")


if __name__ == "__main__":
    for name in ("DeveloperForm.py", "AdminForm.py", "OperForm.py"):
        p = ROOT / name
        if p.is_file():
            migrate_retranslate(p)
    migrate_oper_msgbox(ROOT / "OperForm.py")
