import pytest

from scripts.run import MAP_NAME, resolve_map


class FakeMaps:
    def __init__(self, result):
        self.result = result
        self.requested = None

    def get(self, name):
        self.requested = name
        return self.result


def test_resolve_map_returns_configured_map():
    expected_map = object()
    fake_maps = FakeMaps(expected_map)

    resolved = resolve_map(fake_maps)

    assert resolved is expected_map
    assert fake_maps.requested == MAP_NAME


def test_resolve_map_reports_missing_map_clearly():
    fake_maps = FakeMaps(None)

    with pytest.raises(RuntimeError) as exc_info:
        resolve_map(fake_maps)

    message = str(exc_info.value)
    assert MAP_NAME in message
    assert "/Applications/StarCraft II/Maps/" in message
    assert "scripts/setup_maps.sh" in message
