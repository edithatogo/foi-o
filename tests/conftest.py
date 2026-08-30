"""Shared pytest fixtures and marker semantics.

Markers are declared in ``pyproject.toml`` (unit, integration, mojo, analytics)
plus the trial markers registered here (property, memray). This conftest is
intentionally minimal: it centralises marker semantics and Hypothesis example
profiles without adding global state.
"""

from __future__ import annotations

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register trial-phase markers so strict markers accepts them."""
    config.addinivalue_line("markers", "property: Hypothesis property-based tests")
    config.addinivalue_line("markers", "memray: memory-profiled tests, opt-in via --memray")


try:  # optional dependency: profiles exist only when hypothesis is installed
    from hypothesis import settings

    settings.register_profile("default", max_examples=100, deadline=None)
    settings.register_profile("fast", max_examples=10, deadline=None)
    settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))
except ImportError:  # pragma: no cover
    pass
