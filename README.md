# Spotify To Text

> Export Spotify playlist **metadata** (playlist names, track titles, artists, duration) to JSON or plain text.
> This tool **does not** download audio/content from Spotify. It is designed to comply with the Spotify Developer Terms when used as documented below.

---

# Read these first
- [Spotify Developer Terms](https://developer.spotify.com/terms)
- [Design & Branding](https://developer.spotify.com/documentation/design)

---

# Features
- Export one JSON file per playlist (`playlist_<playlist_id>.json`) containing:
  - `playlist_id`, `playlist_name`, `owner_id`, `total_tracks`, `expires_at`, `tracks` (with `track_id`, `title`, `artists`, `duration_ms`, `duration`)
- Automatic TTL-based expiry (`expires_at`) and purge utilities
- CLI flags for purge, force purge, delete-by-owner, disconnect (remove saved refresh token), and clear `.env`
- Uses OAuth Authorization Code Flow and respects Spotify rate limiting (handles `429 Retry-After`)

---

# Requirements
- Python 3.9+ (adjust in your Pipfile / environment as needed)
- `pipenv` for environment management (or use plain `pip` + virtualenv)
- Packages: `requests`, `python-dotenv`

---

# Installation
Change to the cloned project directory.

Copy
```bash
cp .env.example .env
```

Paste your Spotify tokens in the `.env` fields.

Then follow one of the following installation.

## Installation with pipenv
```bash
# install dependencies
pipenv install
# enter environment
pipenv shell
```

## Installation without pipenv
```bash
python -m venv .venv
# enter environment
source .venv/bin/activate
# install dependencies
pip install requests python-dotenv
```

## After usage
```bash
# quit environment
deactivate
```

# Usage / CLI
Here are some example commands you can run in the python environment.

Run the JSON exporter (interactive playlist selection):
```bash
python src/main.py --out exports
```

Export all playlists in JSON (non-interactive):
```bash
python src/main.py --out exports --all
```

Set custom TTL (in days) at runtime:
```bash
python src/main.py --out exports --all --ttl-days 1
```

Purge expired exports (honors `expires_at`):
```bash
python src/main.py --out exports --purge
```

Force-delete all export JSON files (confirmation required; use `--yes` to skip prompt):
```bash
python src/main.py --out exports --purge-all
```

Delete exports for a specific Spotify user id (`owner_id`):
```bash
python src/main.py --out exports --delete-owner <OWNER_ID>
```

Disconnect (remove saved `SPOTIFY_REFRESH_TOKEN` from `.env`; use `--yes` to skip prompt):
```bash
python src/main.py --disconnect
```

Clear the entire `.env` file (destructive; prompts for confirmation):
```bash
python src/main.py --clear-env
```

To avoid saving the refresh token automatically, run with `--no-save-refresh`.

You can automate the purge with a cron job, for instance.

# Disconnecting & revoking access
1. Remove stored refresh token (use `--disconnect`) or manually remove `SPOTIFY_REFRESH_TOKEN` from `.env`.
2. To fully revoke the app’s access, go to Spotify account web UI → Apps and remove the app’s access. Rotating the app client secret in the Developer Dashboard also invalidates tokens.