"""Unit tests for the core renderer."""

from app.core.renderer import ENV, query_param, render


class TestQueryParam:
    def test_append_without_query(self):
        assert query_param("https://example.com/video", "lang=zh-CN") == (
            "https://example.com/video?lang=zh-CN"
        )

    def test_append_with_query(self):
        assert query_param("https://example.com/video?page=1", "lang=zh-CN") == (
            "https://example.com/video?page=1&lang=zh-CN"
        )

    def test_skip_existing_key(self):
        assert query_param("https://example.com/video?lang=en", "lang=zh-CN") == (
            "https://example.com/video?lang=en"
        )

    def test_keep_fragment(self):
        assert query_param("https://example.com/video#player", "lang=zh-CN") == (
            "https://example.com/video?lang=zh-CN#player"
        )

    def test_registered_filter(self):
        assert ENV.filters["query_param"] is query_param

    def test_render_uses_filter(self):
        result = render(
            "{{ url | query_param('lang=zh-CN') }}",
            {"url": "https://example.com/video?page=1"},
        )
        assert result == "https://example.com/video?page=1&lang=zh-CN"
