"""These unit tests never need the application's database fixtures."""

import pytest


@pytest.fixture(autouse=True)
def analysis_session():
    pass
