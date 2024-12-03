import time

import pytest

from spiderexpress_tiktok.spiderexpress_tiktok import _call_counter_, guard_end_point


def test_guard_endpoint(monkeypatch):
    """Should increase the call counter for the endpoint."""

    @guard_end_point("users_info")
    def some_test_function():
        print("This is a test function")

    # Test the decorator function
    some_test_function()

    assert _call_counter_["users_info"] == 1
    assert _call_counter_["followers"] == 0


def test_guard_sleeping(monkeypatch):
    """Should wait for the reset time."""
    monkeypatch.setattr(
        "spiderexpress_tiktok.spiderexpress_tiktok.call_limits",
        {
            "followers": 1,
            "followings": 1,
            "users_info": 1,
        },
    )
    called = False

    def sleep(x):
        print("I've been called and now I am pretending to be sleeping.")
        nonlocal called
        called = True

    monkeypatch.setattr(time, "sleep", value=sleep)

    @guard_end_point("users_info")
    def some_test_function():
        print("This is a test function")

    # Test the decorator function
    some_test_function()

    assert called is True


def test_guard_endpoint_invalid_endpoint():
    """Should raise an exception for an invalid endpoint."""
    with pytest.raises(ValueError) as exc:

        @guard_end_point("invalid")
        def some_test_function():
            print("This is a test function")

    assert str(exc.value) == "Invalid endpoint: invalid"
