# SPDX-License-Identifier: Apache-2.0
"""Regression checks for leaks that omit the parent-only tracking label."""

from pathlib import Path
import runpy

import pytest

check = runpy.run_path(str(
    Path(__file__).resolve().parents[1] / "integration/diagnosis_checks.py"
))["assert_unbiased_input"]


@pytest.mark.parametrize("text", [
    "The parent thinks TTL expiration is broken.",
    "ttl EXPIRATION\nis broken",
    "TTL expiration: is broken. Confirm this.",
    "Parent-only SECRET_MARKER",
])
def test_rejects_hypothesis_or_marker_leaks(text: str) -> None:
    with pytest.raises(AssertionError, match="leaked"):
        check(text, "SECRET_MARKER", "TTL expiration is broken")


def test_accepts_observations_without_theory() -> None:
    check("North then south returns North guide twice at times 0 and 1.",
          "SECRET_MARKER", "TTL expiration is broken")


def test_encrypted_input_cannot_establish_exclusion() -> None:
    with pytest.raises(AssertionError, match="cannot be audited"):
        check("gAAAAencrypted", "SECRET_MARKER", "TTL expiration is broken")
