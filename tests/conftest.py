"""Test suite configuration and helper functions."""

import pytest


# This auto-used fixtures raises an exception if any test tries to make an HTTP request.
# This is useful to prevent tests from making real HTTP requests.
# https://blog.jerrycodes.com/no-http-requests/
@pytest.fixture(autouse=True)
def no_http_requests(monkeypatch):
    """Prevent tests from making HTTP requests, this will be automatically used in every test.
    All requests will raise an exception.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to monkeypatch things

    Raises:
        RuntimeError: Always raised when a test tries to make an HTTP request
    """

    def urlopen_mock(self, method, url, *args, **kwargs):
        raise RuntimeError(
            f"The test was about to {method} {self.scheme}://{self.host}{url}"
        )

    monkeypatch.setattr(
        "urllib3.connectionpool.HTTPConnectionPool.urlopen", urlopen_mock
    )
