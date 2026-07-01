"""Unit tests for subtitle service helpers."""

import pytest

from app.services.subtitle import SubtitleService


class TestSubtitleService:
    @pytest.mark.parametrize(
        ("label", "language"),
        [
            ("chs", "zh-Hans"),
            ("CHT", "zh-Hant"),
            ("cn", "zh-CN"),
            ("zh", "zh"),
            ("chi", "zh"),
            ("zho", "zh"),
            ("zh-cn", "zh-CN"),
            ("zh_CN", "zh-CN"),
            ("zh-Hans", "zh-Hans"),
            ("zh-tw", "zh-TW"),
            ("zh_Hant", "zh-Hant"),
            ("en", "en"),
            ("eng", "en"),
            ("en-us", "en-US"),
            ("ja", "ja"),
            ("jp", "ja"),
            ("jpn", "ja"),
            ("ja-jp", "ja-JP"),
            ("fr-fr", "fr-FR"),
            ("fre", "fr"),
            ("deu", "de"),
            ("ger", "de"),
            ("ko-kr", "ko-KR"),
            ("pt_BR", "pt-BR"),
            ("spa", "es"),
            ("es-419", "es-419"),
        ],
    )
    def test_external_track_language_standardizes_language_tags(
        self, label: str, language: str
    ):
        assert SubtitleService._external_track_language(label) == language

    @pytest.mark.parametrize("label", ["subtitle", "C.UTF-8", "zh-普通话"])
    def test_external_track_language_ignores_invalid_language_tags(self, label: str):
        assert SubtitleService._external_track_language(label) is None
