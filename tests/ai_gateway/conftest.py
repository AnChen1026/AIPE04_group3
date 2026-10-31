"""Model gateway and state tests do not access the application database."""

import pytest


@pytest.fixture(autouse=True)
def analysis_session():
    pass
