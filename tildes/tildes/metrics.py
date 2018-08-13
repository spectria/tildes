"""Contains Prometheus metric objects and functions for instrumentation."""

# The prometheus_client classes work in a pretty crazy way, need to disable these pylint
# checks to avoid errors
# pylint: disable=no-value-for-parameter,redundant-keyword-arg

from typing import Callable

from prometheus_client import Counter, Histogram
from prometheus_client.core import _LabelWrapper


_COUNTERS = {
    "votes": Counter("tildes_votes_total", "Votes", labelnames=["target_type"]),
    "comments": Counter("tildes_comments_total", "Comments"),
    "invite_code_failures": Counter(
        "tildes_invite_code_failures_total", "Invite Code Failures"
    ),
    "logins": Counter("tildes_logins_total", "Login Attempts"),
    "login_failures": Counter("tildes_login_failures_total", "Login Failures"),
    "messages": Counter("tildes_messages_total", "Messages", labelnames=["type"]),
    "registrations": Counter("tildes_registrations_total", "User Registrations"),
    "topics": Counter("tildes_topics_total", "Topics", labelnames=["type"]),
    "subscriptions": Counter("tildes_subscriptions_total", "Subscriptions"),
    "unsubscriptions": Counter("tildes_unsubscriptions_total", "Unsubscriptions"),
}

_HISTOGRAMS = {
    "markdown_processing": Histogram(
        "tildes_markdown_processing_seconds",
        "Markdown processing",
        buckets=[.001, .0025, .005, .01, 0.025, .05, .1, .5, 1.0],
    ),
    "comment_tree_sorting": Histogram(
        "tildes_comment_tree_sorting_seconds",
        "Comment tree sorting time",
        labelnames=["num_comments_range", "order"],
        buckets=[.00001, .0001, .001, .01, .05, .1, .5, 1.0],
    ),
}


def incr_counter(name: str, amount: int = 1, **labels: str) -> None:
    """Increment a Prometheus counter."""
    try:
        counter = _COUNTERS[name]
    except KeyError:
        raise ValueError("Invalid counter name")

    if isinstance(counter, _LabelWrapper):
        counter = counter.labels(**labels)

    counter.inc(amount)


def get_histogram(name: str, **labels: str) -> Histogram:
    """Return an (optionally labeled) Prometheus histogram by name."""
    try:
        hist = _HISTOGRAMS[name]
    except KeyError:
        raise ValueError("Invalid histogram name")

    if isinstance(hist, _LabelWrapper):
        hist = hist.labels(**labels)

    return hist


def histogram_timer(name: str) -> Callable:
    """Return the .time() decorator for a Prometheus histogram."""
    return get_histogram(name).time()
