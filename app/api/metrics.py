"""Application-specific Prometheus metrics."""

from prometheus_client import Counter


RESOLVER_REQUESTS = Counter(
    "resolver_requests",
    "Resolver requests by endpoint, outcome, and response mode.",
    ("endpoint", "outcome", "response_mode"),
)


def record_resolver_outcome(
    endpoint: str, outcome: str, response_mode: str
) -> None:
    """Record the product outcome of one resolver request.

    HTTP status codes retain their protocol meaning, while this metric separates
    expected user-facing outcomes (such as an HTML interstitial) from failures
    that need operational attention.
    """
    RESOLVER_REQUESTS.labels(
        endpoint=endpoint, outcome=outcome, response_mode=response_mode
    ).inc()


def record_legacy_url_resolver_outcome(outcome: str, response_mode: str) -> None:
    """Record an outcome for the ``/legacy`` endpoint."""
    record_resolver_outcome("legacy_url", outcome, response_mode)
