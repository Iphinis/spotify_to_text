"""
Exports playlists and tracks to JSON using spotify_api and utils helpers.
Writes one JSON file per playlist and includes an expires_at timestamp for TTL-based purge.
"""
import json
import os
from datetime import datetime, timezone, timedelta
from utils import ms_to_hhmmss, now_iso_utc
from spotify_api import paged_get

API_BASE = "https://api.spotify.com/v1"


def export_playlists_and_tracks(access_token, out_path, export_all=False, ttl_days=2):
    """Retrieve playlists and tracks and write per-playlist JSON files into the output directory.
    out_path can be a directory; by default 'exports/'. Returns a dict summary.
    """
    out_dir = out_path if os.path.isdir(out_path) else os.path.dirname(out_path) or 'exports'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    print("Fetching playlists...")
    playlists_raw = paged_get(f"{API_BASE}/me/playlists", access_token, params={"limit": 50})
    playlists = []
    for p in playlists_raw:
        playlist_id = p.get('id')
        name = p.get('name')
        owner_id = p.get('owner', {}).get('id')
        total = p.get('tracks', {}).get('total', 0)
        playlists.append({
            'id': playlist_id,
            'name': name,
            'owner_id': owner_id,
            'total_tracks': total
        })

    if not playlists:
        print('No playlists found for this user.')
        return None

    selected = playlists if export_all else []
    if not export_all:
        print('Playlists found:')
        for idx, pl in enumerate(playlists):
            print(f"[{idx}] {pl['name']} (tracks: {pl['total_tracks']})")
        choice = input("Enter indices separated by commas, or 'a' to export all: ").strip()
        if choice.lower() in ('a', 'all'):
            selected = playlists
        else:
            try:
                indices = [int(x.strip()) for x in choice.split(',') if x.strip() != '']

                if any([i < 0 or i >= len(playlists) for i in indices]):
                    raise IndexError

                for i in indices:
                    selected.append(playlists[i])
            except Exception:
                print('Invalid selection - aborting.')
                return None

    summary = {"exported_at": now_iso_utc(), "exports": []}
    for pl in selected:
        print(f"Processing playlist: {pl['name']} (id={pl['id']}) - {pl['total_tracks']} tracks")
        tracks_items = paged_get(f"{API_BASE}/playlists/{pl['id']}/tracks", access_token, params={"limit": 100})
        tracks_out = []
        for item in tracks_items:
            track = item.get('track') if isinstance(item, dict) and 'track' in item else item
            if not track:
                continue
            track_id = track.get('id')
            title = track.get('name')
            artists = [a.get('name') for a in track.get('artists', []) or [] if a.get('name')]
            duration_ms = track.get('duration_ms')
            tracks_out.append({
                'track_id': track_id,
                'title': title,
                'artists': artists,
                'duration_ms': duration_ms,
                'duration': ms_to_hhmmss(duration_ms)
            })

        expires_at = (datetime.now(timezone.utc) + timedelta(days=int(ttl_days))).strftime('%Y-%m-%dT%H:%M:%SZ')
        playlist_output = {
            'playlist_id': pl['id'],
            'playlist_name': pl['name'],
            'owner_id': pl.get('owner_id'),
            'total_tracks': pl['total_tracks'],
            'expires_at': expires_at,
            'tracks': tracks_out
        }

        # write per-playlist file named by playlist id
        filename = f"playlist_{pl['id']}.json"
        file_path = os.path.join(out_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(playlist_output, f, ensure_ascii=False, indent=2)
        print(f" -> wrote {file_path} ({len(tracks_out)} tracks)")
        summary['exports'].append({'playlist_id': pl['id'], 'file': file_path, 'expires_at': expires_at})

    # also write a summary file
    summary_path = os.path.join(out_dir, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Export completed. Summary: {summary_path}")
    return summary
