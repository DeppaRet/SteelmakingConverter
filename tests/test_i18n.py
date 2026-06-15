"""Tests for i18n module."""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class TestI18n(unittest.TestCase):
    def test_tr_returns_russian_by_default(self):
        from i18n import tr
        with patch("i18n.get_language", return_value="ru"):
            self.assertEqual(tr("Test", "Авторизация"), "Авторизация")

    def test_tr_returns_english_when_en(self):
        from i18n import tr, reload_translations
        reload_translations()
        with patch("i18n.get_language", return_value="en"):
            self.assertEqual(tr("LoginForm", "Авторизация"), "Authorization")

    def test_tr_fallback_unknown(self):
        from i18n import tr
        with patch("i18n.get_language", return_value="en"):
            self.assertEqual(tr("X", "Неизвестная строка XYZ"), "Неизвестная строка XYZ")

    def test_get_language_default_ru(self):
        from locale_settings import normalize_language, LANG_RU
        self.assertEqual(normalize_language(None), LANG_RU)
        self.assertEqual(normalize_language("ru"), LANG_RU)

    def test_tr_table_labels_en(self):
        from i18n import tr, reload_translations, canonical_label
        reload_translations()
        with patch("i18n.get_language", return_value="en"):
            self.assertEqual(tr("OperatorForm", "Чугун жидкий"), "Liquid hot metal")
            self.assertEqual(tr("OperatorForm", "Лом"), "Scrap")
            self.assertEqual(
                canonical_label("Liquid hot metal"),
                "Чугун жидкий",
            )

    def test_tr_recommendations_en(self):
        from i18n import tr, reload_translations
        reload_translations()
        with patch("i18n.get_language", return_value="en"):
            self.assertIn(
                "Increase magnesian flux",
                tr(
                    "OperatorForm",
                    "Необходимо увеличить количество магнезиального флюса на 50 кг и заново произвести расчёты",
                ),
            )

    def test_tr_heat_result_labels_en(self):
        from i18n import tr, reload_translations
        reload_translations()
        with patch("i18n.get_language", return_value="en"):
            self.assertEqual(tr("OperatorForm", "Т жидкого металла, °C"), "Liquid metal T, °C")
            self.assertEqual(tr("OperatorForm", "Выбросы CO2 [кг]:"), "CO2 emissions [kg]:")
            self.assertEqual(tr("OperatorForm", "Масса стали [кг]:"), "Steel mass [kg]:")

    def test_translations_file_valid_json(self):
        path = ROOT / "i18n" / "translations_en.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)
        self.assertIn("Авторизация", data)


if __name__ == "__main__":
    unittest.main()
