"""Fixtures for the custom foods and recipes tests (Plan 12 slice 4). The real consent gate
runs here (terms)."""

from uuid import uuid4

import pytest

from tests.api.foods.conftest import (  # noqa: F401  (shared fixtures)
    ACC_A,
    ACC_B,
    G1_SETTINGS,
    OFF_BARCODE,
    FakeOff,
    accounts,
    clock,
    consented,
    fake_off,
    g1,
    grant,
    login,
    make_food,
    portion,
    set_primary,
    settings,
    today,
)

BAR = {
    "name": "Protein bar",
    "basis": "g",
    "values_per": "100",
    "nutrients": {"energy_kcal": 400, "protein_g": 30, "carbs_g": 40, "fat_g": 12},
}


def bar(**cols) -> dict:
    return BAR | cols


@pytest.fixture
def cid() -> str:
    return str(uuid4())
