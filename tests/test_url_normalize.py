"""URL normalization tests."""

from immich_auto_stacker.url_normalize import normalize_immich_base_url


def test_strip_trailing_slash() -> None:
    assert normalize_immich_base_url("https://photos.example.com/") == (
        "https://photos.example.com"
    )


def test_strip_api_suffix() -> None:
    assert normalize_immich_base_url("https://photos.example.com/api") == (
        "https://photos.example.com"
    )


def test_strip_api_with_slash() -> None:
    assert normalize_immich_base_url("https://photos.example.com/api/") == (
        "https://photos.example.com"
    )
