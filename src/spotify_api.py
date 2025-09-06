"""
Contains wrappers for Spotify Web API calls (GET + paging) and rate-limit handling.
"""
import requests
import time


def handle_rate_limit(resp):
    if resp.status_code == 429:
        retry = int(resp.headers.get('Retry-After', '1'))
        print(f"Rate limited by Spotify API. Waiting {retry} seconds...")
        time.sleep(retry + 1)
        return True
    return False


def spotify_get(url, token, params=None):
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if handle_rate_limit(resp):
            continue
        if resp.status_code >= 400:
            raise RuntimeError(f"Spotify API error {resp.status_code}: {resp.text}")
        return resp.json()


def paged_get(url, token, params=None):
    items = []
    next_url = url
    local_params = None if params is None else dict(params)
    while next_url:
        data = spotify_get(next_url, token, params=local_params)
        local_params = None
        if isinstance(data, dict):
            if 'items' in data:
                items.extend(data['items'])
            elif 'tracks' in data and isinstance(data['tracks'], dict) and 'items' in data['tracks']:
                items.extend(data['tracks']['items'])
            else:
                return data
            next_url = data.get('next')
        else:
            break
    return items
