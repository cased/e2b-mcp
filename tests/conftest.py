"""
Pytest configuration for e2b-mcp tests.
"""
import pytest
import os


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle integration test markers."""
    skip_integration = pytest.mark.skip(reason="need E2B_API_KEY to run integration tests")

    for item in items:
        if "integration" in item.keywords:
            # Skip integration tests if E2B_API_KEY not set
            if not os.getenv("E2B_API_KEY"):
                item.add_marker(skip_integration)