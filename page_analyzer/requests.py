import requests


def fetch_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return response
