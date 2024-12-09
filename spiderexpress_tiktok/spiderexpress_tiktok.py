"""This module contains the SpiderExpress plugins for fetching TikTok data.

Constants:
    call_limits (Dict): The call limits for the TikTok API.
    ACCESS_TOKEN (AccessToken): The access token for the TikTok API.
"""

import datetime
import functools
import time
from typing import Dict, List, Tuple

import pandas as pd
from loguru import logger
from researchtikpy import AccessToken, get_followers, get_following, get_users_info
from spiderexpress import PlugIn

call_limits = {
    "followers": 20000,
    "followings": 20000,
    "users_info": 1000,
}

_call_counter_ = {
    "followers": 0,
    "followings": 0,
    "users_info": 0,
}

ACCESS_TOKEN = None


def _get_access_token_(key: str, secret: str) -> AccessToken:
    """This function returns the access token for the TikTok API.

    Returns:
        AccessToken: The access token for the TikTok API.
    """
    global ACCESS_TOKEN  # pylint: disable=W0603
    if ACCESS_TOKEN is None:
        logger.info("Requesting new access token.")
        ACCESS_TOKEN = AccessToken(
            client_key=key,
            client_secret=secret,
        )
    logger.info("Using access token: {ACCESS_TOKEN}.")
    return ACCESS_TOKEN


def _reset_date_() -> datetime.datetime:
    """This function returns the next reset time for the TikTok API.

    Returns:
        datetime.datetime: The next reset time for the TikTok API.
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    # Next reset time is 12am UTC time
    if now >= noon:  # If it is past 12am, then the next reset time is tomorrow
        return noon + datetime.timedelta(days=1)
    return noon


def _get_reset_seconds_(reset_date: datetime.datetime) -> int:
    """This function returns the number of seconds until the next reset time for the TikTok API.

    Returns:
        int: The number of seconds until the next reset time for the TikTok API.
    """
    return (reset_date - datetime.datetime.now(datetime.timezone.utc)).total_seconds()


def guard_end_point(endpoint: str):
    """This function is a decorator that guards the TikTok API endpoints.

    Parameters:
        endpoint (str): The TikTok API endpoint to guard.

    Returns:
        function: The decorated function.

    Raises:
        ValueError: If the endpoint is invalid.
    """
    if endpoint not in call_limits:
        raise ValueError(f"Invalid endpoint: {endpoint}")

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if _call_counter_[endpoint] >= call_limits[endpoint]:
                reset_date = _reset_date_()
                seconds_until_reset = _get_reset_seconds_(reset_date)

                logger.info(
                    f"Waiting for {seconds_until_reset} seconds until"
                    "reset at {reset_date.isoformat()}"
                )

                time.sleep(seconds_until_reset)

                _call_counter_[endpoint] = 0
            else:
                _call_counter_[endpoint] += 1
            return func(*args, **kwargs)

        return wrapper

    return decorator


@functools.cache
@guard_end_point("users_info")
def _users_info_(handle: str, token: AccessToken) -> pd.DataFrame:
    """This is a SpiderExpress plugin entrypoint for fetching user info"""
    data = get_users_info([handle], token, verbose=False)
    data["name"] = handle
    return data


@guard_end_point("followers")
def _followers_(
    handles: List[str], configuration: Dict
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """This is a SpiderExpress plugin entrypoint for fetching followers"""
    token = _get_access_token_(
        configuration["client_key"],
        configuration["client_secret"],
    )
    total_count = configuration.get("total_count", 1500)
    all_followers = get_followers(
        handles, token, max_count=100, total_count=total_count
    )
    all_nodes = (
        (
            pd.concat([all_followers.username, all_followers.target_account])
            .unique()
            .tolist()
        )
        if configuration.get("fetch_all", False)
        else handles
    )
    user_info = pd.concat(
        [_users_info_(handle=handle, token=token) for handle in all_nodes]
    )
    return all_followers, user_info


@guard_end_point("followings")
def _followings_(
    handles: List[str], configuration: Dict
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """This is a SpiderExpress plugin entrypoint for fetching followings"""
    token = _get_access_token_(
        configuration["client_key"],
        configuration["client_secret"],
    )
    # total_count = config.get("total_count", 1500)
    all_followings = get_following(
        handles,
        token,
        max_count=100,  # total_count=total_count
    )
    all_nodes = (
        (
            pd.concat([all_followings.username, all_followings.target_account])
            .unique()
            .tolist()
        )
        if configuration.get("fetch_all", False) is True
        else handles
    )
    user_info = pd.concat(
        [_users_info_(handle=handle, token=token) for handle in all_nodes]
    )
    return all_followings, user_info


followers_entrypoint = PlugIn(
    default_configuration={
        "client_key": "INSERT_YOUR_CLIENT_KEY",
        "client_secret": "INSERT_YOUR_CLIENT_SECRET",
        "total_count": 1500,
        "fetch_all": True,
    },
    callable=_followers_,
    tables={"edges": {}, "nodes": {}},
    metadata={},
)

followings_entrypoint = PlugIn(
    default_configuration={
        "client_key": "INSERT_YOUR_CLIENT_KEY",
        "client_secret": "INSERT_YOUR_CLIENT_SECRET",
        "total_count": 1500,
        "fetch_all": True,
    },
    callable=_followings_,
    tables={"edges": {}, "nodes": {}},
    metadata={},
)
