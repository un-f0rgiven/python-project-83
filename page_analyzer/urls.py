from urllib.parse import urlparse, urlunparse
import validators


def normalize_url(url):
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc.strip().lower()
    normalized_url = urlunparse((parsed_url.scheme, netloc, "", "", "", ""))
    return normalized_url


def is_valid_url(url):
    if len(url) > 255:
        return False
    return validators.url(url)
