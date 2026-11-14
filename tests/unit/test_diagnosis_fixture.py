# SPDX-License-Identifier: Apache-2.0
"""Validate the diagnostic fixture, not the behavior of a language model."""

from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[2]
Catalog = runpy.run_path(str(ROOT / "tests/fixtures/diagnosis/catalog.py"))["Catalog"]


@pytest.mark.parametrize("ttl", [60, 3600])
def test_collision_occurs_before_expiration(ttl: int) -> None:
    catalog = Catalog(ttl=ttl)
    assert catalog.lookup("north", "guide", now=0) == "North guide"
    # This is the bug presented to the diagnostic agent, not expected product behavior.
    assert catalog.lookup("south", "guide", now=1) == "North guide"


def test_reversing_request_order_changes_which_tenant_receives_wrong_data() -> None:
    catalog = Catalog()
    assert catalog.lookup("south", "guide", now=0) == "South guide"
    assert catalog.lookup("north", "guide", now=1) == "South guide"


def test_expiration_refreshes_value_but_does_not_remove_collision() -> None:
    catalog = Catalog()
    catalog.lookup("north", "guide", now=0)
    assert catalog.lookup("south", "guide", now=60) == "South guide"
    assert catalog.lookup("north", "guide", now=61) == "South guide"
