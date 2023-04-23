"""Central place for all HTTP-handling."""

from apptk.http import HttpClient
from requests_ratelimiter import LimiterAdapter

DEFAULT_ADAPTER = LimiterAdapter(per_second=5)
ADAPTERS = {
    "http://": DEFAULT_ADAPTER,
    "https://": DEFAULT_ADAPTER,
}


def add_rate_limit(hostname: str, rate_per_second: int) -> None:
    """
    Add a rate limit on the number of requests per second to a specific hostname.

    :param hostname: The hostname to set the rate limit for.
    :param rate_per_second: The number of requests per second to limit to.
    """
    adapter = LimiterAdapter(per_second=rate_per_second)
    ADAPTERS[f"https://{hostname}"] = adapter
    ADAPTERS[f"http://{hostname}"] = adapter


def get_client(*args, **kwargs) -> HttpClient:
    """Return a HttpClient instance with rate limiter adapters attached."""
    kwargs.setdefault("use_cloudscraper", True)
    user_agent = kwargs.pop("user_agent", None)
    client = HttpClient(*args, **kwargs)
    if user_agent:
        client._session.headers["User-Agent"] = user_agent
    # for key, adapter in ADAPTERS.items():
    #     client._session.mount(key, adapter)
    return client
