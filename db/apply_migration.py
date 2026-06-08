"""Применяет SQL-миграцию к базе regimdata.

Использование:
    python db/apply_migration.py [путь_к_sql]

По умолчанию применяется db/migration_stoichiometry.sql к localhost/root/root.
Скрипт идемпотентный — повторный запуск безопасен.
"""
import os
import sys

import mysql.connector as mc

DB_HOST = "localhost"
DB_LOGIN = "root"
DB_PASS = "root"
DB_NAME = "regimdata"


def split_statements(sql_text):
    """Разбивает SQL на отдельные операторы, игнорируя строки-комментарии."""
    lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    return [s.strip() for s in cleaned.split(";") if s.strip()]


def main():
    sql_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "migration_stoichiometry.sql"
    )
    with open(sql_path, "r", encoding="utf-8") as fh:
        sql_text = fh.read()

    statements = split_statements(sql_text)
    db = mc.connect(host=DB_HOST, user=DB_LOGIN, password=DB_PASS, database=DB_NAME)
    cur = db.cursor()
    for i, stmt in enumerate(statements, 1):
        try:
            cur.execute(stmt)
            cur.fetchall() if cur.with_rows else None
        except mc.Error as err:
            print(f"[{i}] ОШИБКА в операторе:\n{stmt[:200]}\n  -> {err}")
            raise
    db.commit()
    cur.close()
    db.close()
    print(f"Применено операторов: {len(statements)}")


if __name__ == "__main__":
    main()
