"""Functions related to URLs."""

from urllib.parse import urlparse


def get_domain_from_url(url: str, strip_www: bool = True) -> str:
    """Return the domain name from a url."""
    domain = urlparse(url).netloc

    if not domain:
        raise ValueError('Invalid url or domain could not be determined')

    if strip_www and domain.startswith('www.'):
        domain = domain[4:]

    return domain
