"""Shared HTTP retry session for resilient API calls."""

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def create_retry_session(retries=3, backoff_factor=1.0,
                          status_forcelist=(429, 500, 502, 503, 504),
                          timeout=30):
    """Create a requests session with automatic retry logic.

    Args:
        retries: Number of retries
        backoff_factor: Exponential backoff factor (1s, 2s, 4s)
        status_forcelist: HTTP status codes to retry on
        timeout: Default timeout in seconds

    Returns:
        requests.Session with retry adapter mounted
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session._default_timeout = timeout
    return session


def get_with_retry(session, url, **kwargs):
    """GET request using the retry session with default timeout."""
    if 'timeout' not in kwargs:
        kwargs['timeout'] = getattr(session, '_default_timeout', 30)
    return session.get(url, **kwargs)
