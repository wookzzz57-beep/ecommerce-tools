import tempfile
from pathlib import Path
import unittest

from firstwindow.i18n import (
    TRANSLATIONS,
    load_language,
    normalize_language,
    save_language,
    translate,
)


class I18nTests(unittest.TestCase):
    def test_normalizes_supported_locales(self):
        self.assertEqual(normalize_language("zh_CN"), "zh-CN")
        self.assertEqual(normalize_language("zh-Hans-CN"), "zh-CN")
        self.assertEqual(normalize_language("en_US"), "en")
        self.assertEqual(normalize_language("fr_FR"), "en")

    def test_missing_preference_uses_system_locale(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            self.assertEqual(load_language(path, system_locale="zh_CN"), "zh-CN")
            self.assertEqual(load_language(path, system_locale="en_US"), "en")

    def test_language_preference_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            save_language("zh-CN", path)
            self.assertEqual(load_language(path, system_locale="en_US"), "zh-CN")
            save_language("en", path)
            self.assertEqual(load_language(path, system_locale="zh_CN"), "en")

    def test_translation_catalogs_have_identical_keys(self):
        self.assertEqual(set(TRANSLATIONS["en"]), set(TRANSLATIONS["zh-CN"]))

    def test_known_translation_and_fallback(self):
        self.assertEqual(translate("zh-CN", "button.one_click_ready"), "一键就绪")
        self.assertEqual(translate("en", "button.one_click_ready"), "Make Me Ready")
        self.assertEqual(translate("zh-CN", "missing.key"), "missing.key")


if __name__ == "__main__":
    unittest.main()
