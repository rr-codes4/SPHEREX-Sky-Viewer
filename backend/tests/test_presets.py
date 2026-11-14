import json
from pathlib import Path

import pytest

from astronomy_backend.exceptions import PresetValidationError
from astronomy_backend.presets import load_presets, validate_preset


def _preset(target_id: str = "target-1") -> dict[str, object]:
    return {
        "target_id": target_id,
        "name": "Example Target",
        "ra": 12.5,
        "dec": -4.25,
        "coordinate_unit": "deg",
        "radius": 6,
        "radius_unit": "arcmin",
        "collection": "spherex_dr1",
        "time_start": "2020-01-01T00:00:00",
        "time_end": "2020-01-02T00:00:00",
    }


def test_valid_preset_converts_to_query() -> None:
    preset = validate_preset(_preset())
    query = preset.to_query()
    assert query.collection == "spherex_dr1"
    assert query.radius_degrees == pytest.approx(0.1)


@pytest.mark.parametrize(
    "change",
    [
        {"dec": 91},
        {"coordinate_unit": "m"},
        {"radius": 0},
        {"time_start": "2021-01-01", "time_end": "2020-01-01"},
        {"collection": "not valid"},
    ],
)
def test_invalid_preset_is_rejected(change: dict[str, object]) -> None:
    data = _preset()
    data.update(change)
    with pytest.raises(PresetValidationError):
        validate_preset(data)


def test_load_presets_rejects_duplicate_ids_and_bad_json(tmp_path: Path) -> None:
    path = tmp_path / "presets.json"
    path.write_text(json.dumps([_preset(), _preset()]), encoding="utf-8")
    with pytest.raises(PresetValidationError):
        load_presets(path)
    path.write_text("{", encoding="utf-8")
    with pytest.raises(PresetValidationError):
        load_presets(path)


def test_missing_required_preset_field_is_rejected() -> None:
    data = _preset()
    del data["target_id"]
    with pytest.raises(PresetValidationError):
        validate_preset(data)
