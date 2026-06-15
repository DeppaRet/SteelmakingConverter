"""Add tr() to table name comparisons in AdminForm and DeveloperForm."""
import re
from pathlib import Path

TABLE_NAMES = [
    "Режимы", "Сталь", "Состав стали", "Чугун", "Состав чугуна",
    "Лом", "Состав лома", "Флюсы", "Пользователи", "Роли",
    "Оператор", "Администратор", "Разработчик модели",
]

ROLE_CONTEXT = {
    "AdminForm.py": "AdminFom",
    "DeveloperForm.py": "Form",
}

for fname in ("AdminForm.py", "DeveloperForm.py"):
    path = Path(__file__).resolve().parent.parent / fname
    text = path.read_text(encoding="utf-8")
    ctx = ROLE_CONTEXT[fname]
    if f'from i18n import tr' not in text and "import tr" not in text.split("class")[0]:
        text = text.replace(
            "import app_theme",
            "import app_theme\nfrom i18n import tr",
        )
    for name in TABLE_NAMES:
        text = text.replace(
            f'== "{name}"',
            f'== tr("{ctx}", "{name}")',
        )
        text = text.replace(
            f'== "{name}"',
            f'== tr("{ctx}", "{name}")',
        )
        text = text.replace(
            f'(chTable == "{name}")',
            f'(chTable == tr("{ctx}", "{name}"))',
        )
    path.write_text(text, encoding="utf-8")
    print(f"Updated {fname}")
