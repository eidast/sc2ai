import pytest

from scripts.run import DEFAULT_MAP, resolve_map


class FakeMaps:
    def __init__(self, result=None):
        self.result = result
        self.requested = None
        self._keys = ["AcropolisLE", "ThunderbirdLE"] if result else []

    def get(self, name):
        self.requested = name
        return self.result

    def keys(self):
        return self._keys

    def __iter__(self):
        return iter(self._keys)


def test_resolve_map_returns_configured_map():
    expected_map = object()
    fake_maps = FakeMaps(expected_map)
    fake_maps._keys = [DEFAULT_MAP]

    resolved = resolve_map(DEFAULT_MAP, fake_maps)

    assert resolved is expected_map
    assert fake_maps.requested == DEFAULT_MAP


def test_resolve_map_reports_missing_map_clearly():
    fake_maps = FakeMaps(None)

    with pytest.raises(RuntimeError) as exc_info:
        resolve_map("NonExistentMap", fake_maps)

    message = str(exc_info.value)
    assert "NonExistentMap" in message
    assert "/Applications/StarCraft II/Maps/" in message
    assert "scripts/setup_maps.sh" in message


def test_resolve_map_random_selects_map():
    fake_maps = FakeMaps(object())
    fake_maps._keys = ["AcropolisLE", "ThunderbirdLE"]

    resolved = resolve_map("random", fake_maps)

    assert resolved is not None
    assert fake_maps.requested in ("AcropolisLE", "ThunderbirdLE")
