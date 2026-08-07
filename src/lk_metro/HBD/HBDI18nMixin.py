import json
from pathlib import Path

from utils_future import Log

from lk_metro.Route import Route

log = Log("HBD")


class HBDI18nMixin:
    LANGUAGES = ("si", "ta")
    LANGUAGE_NAMES = {"si": "Sinhala", "ta": "Tamil"}

    def _load_translations(
        self,
        data_dir: Path,
        language: str | None,
    ) -> dict[str, str]:
        if language is None:
            return {}
        if language not in self.LANGUAGES:
            raise ValueError(f"Unsupported HBD language: {language}")
        records = json.loads(
            (data_dir / "i18n.json").read_text(encoding="utf-8")
        )
        field = f"name_{language}"
        return {
            record["name_en"]: record[field]
            for record in records
            if isinstance(record.get(field), str) and record[field]
        }

    def _stop_label(self, stop_name: str) -> str:
        return self._translated_text(stop_name)

    def _translated_text(self, text: str) -> str:
        translated = self._translations.get(text)
        if translated is not None or self.language is None:
            return translated or text
        if text not in self._missing_translation_warnings:
            language_name = self.LANGUAGE_NAMES[self.language]
            log.warning(f"Missing {language_name} translation for {text!r}")
            self._missing_translation_warnings.add(text)
        return text

    def _footer_text(self) -> str:
        text = self._translated_text(self.FOOTER_TEXT)
        return f"{text} · {self.MAP_VERSION}"

    def _legend_route_name(self, route: Route) -> str:
        if not self._translations:
            return route.name
        names = [name for name in self._translations if name in route.name]
        names.sort(key=route.name.index)
        return " - ".join(self._translations[name] for name in names)
