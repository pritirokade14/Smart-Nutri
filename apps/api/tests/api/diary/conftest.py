"""Fixtures for the diary routes (Plan 11). The real consent gate runs here.

The clock is pinned to 2026-11-07 12:00 IST; the primary member is the G1 profile (via `g1`)
or the G2 profile (via `g2`), as in the targets tests.
"""

from tests.api.conftest import clock  # noqa: F401  (pinned clock)
from tests.api.targets.conftest import (  # noqa: F401  (shared fixtures)
    ACC_A,
    ACC_B,
    ACC_C,
    G1_BODY,
    G1_SETTINGS,
    G2_BODY,
    G2_SETTINGS,
    TODAY,
    add_member,
    consented,
    g1,
    g2,
    grant,
    login,
    set_primary,
    today,
)

YESTERDAY = "2026-11-06"
