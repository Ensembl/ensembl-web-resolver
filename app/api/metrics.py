"""Application-specific Prometheus metrics."""

from prometheus_client import Counter


LEGACY_URL_RESOLVER_REQUESTS = Counter(
    "legacy_url_resolver_requests",
    "Legacy URL resolver requests by outcome and response mode.",
    ("outcome", "response_mode"),
)


def record_legacy_url_resolver_outcome(outcome: str, response_mode: str) -> None:
    """Record the product outcome of one legacy resolver request.

    HTTP status codes retain their protocol meaning, while this metric separates
    expected user-facing outcomes (such as an HTML interstitial) from failures
    that need operational attention.
    """
    LEGACY_URL_RESOLVER_REQUESTS.labels(
        outcome=outcome, response_mode=response_mode
    ).inc()
