"""
Utilities to purge expired exports and delete exports for a user (owner_id).
Also provides purge_all_exports that force-deletes all playlist JSON files.
"""
import os
import json
from datetime import datetime, timezone


def purge_expired_exports(export_dir):
    """Remove JSON files in export_dir whose expires_at is in the past.
    Returns list of removed file paths."""
    removed = []
    if not os.path.isdir(export_dir):
        return removed
    for fname in os.listdir(export_dir):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(export_dir, fname)
        # skip summary file
        if os.path.basename(path) == 'summary.json':
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            expires = data.get('expires_at')
            if not expires:
                continue
            exp_dt = datetime.strptime(expires, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= exp_dt:
                os.remove(path)
                removed.append(path)
                print('Purged:', path)
        except Exception as e:
            print('Failed to process', path, e)
    return removed


def delete_exports_for_owner(export_dir, owner_id):
    """Delete any export files in export_dir belonging to owner_id.
    Returns list of deleted file paths."""
    deleted = []
    if not os.path.isdir(export_dir):
        return deleted
    for fname in os.listdir(export_dir):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(export_dir, fname)
        if os.path.basename(path) == 'summary.json':
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('owner_id') == owner_id:
                os.remove(path)
                deleted.append(path)
                print('Deleted:', path)
        except Exception as e:
            print('Failed to process', path, e)
    return deleted


def purge_all_exports(export_dir):
    """Force-delete all playlist_*.json files and summary.json in export_dir.
    Returns list of removed paths."""
    removed = []
    if not os.path.isdir(export_dir):
        return removed
    for fname in os.listdir(export_dir):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(export_dir, fname)
        try:
            os.remove(path)
            removed.append(path)
            print('Removed:', path)
        except Exception as e:
            print('Failed to remove', path, e)
    return removed
