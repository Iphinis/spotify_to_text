"""
Utilities to purge expired exports and delete exports for a user (owner_id).
Also provides purge_all_exports that force-deletes all playlist JSON files.
"""
# Replace these three functions in src/spotify_export/purge_utils.py

import os
import json
from datetime import datetime, timezone

def _remove_file_if_exists(path, removed_list):
    """Helper: remove path if exists and append to removed_list; ignore missing files."""
    try:
        if os.path.exists(path):
            os.remove(path)
            removed_list.append(path)
            print('Removed:', path)
    except Exception as e:
        print('Failed to remove', path, e)


def purge_expired_exports(export_dir):
    """
    Remove JSON files in export_dir whose expires_at is in the past.
    Also remove matching plain-text sibling files (same base name, .txt).
    Returns list of removed file paths.
    """
    removed = []
    if not os.path.isdir(export_dir):
        return removed

    for fname in os.listdir(export_dir):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(export_dir, fname)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            expires = data.get('expires_at')
            if not expires:
                continue
            exp_dt = datetime.strptime(expires, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= exp_dt:
                # remove the json
                _remove_file_if_exists(path, removed)
                # remove sibling txt if present (same base name)
                base = os.path.splitext(path)[0]
                txt_path = base + '.txt'
                _remove_file_if_exists(txt_path, removed)
        except Exception as e:
            print('Failed to process', path, e)
    return removed


def delete_exports_for_owner(export_dir, owner_id):
    """
    Delete any export files in export_dir belonging to owner_id.
    Also deletes matching .txt sibling files next to each .json.
    Returns list of deleted file paths.
    """
    deleted = []
    if not os.path.isdir(export_dir):
        return deleted

    for fname in os.listdir(export_dir):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(export_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('owner_id') == owner_id:
                # remove json and matching txt
                _remove_file_if_exists(path, deleted)
                base = os.path.splitext(path)[0]
                txt_path = base + '.txt'
                _remove_file_if_exists(txt_path, deleted)
        except Exception as e:
            print('Failed to process', path, e)
    return deleted


def purge_all_exports(export_dir):
    """
    Force-delete all .json and .txt files in export_dir
    Returns list of removed paths.
    """
    removed = []
    if not os.path.isdir(export_dir):
        return removed

    for fname in os.listdir(export_dir):
        # target both json and txt files
        if not (fname.endswith('.json') or fname.endswith('.txt')):
            continue
        path = os.path.join(export_dir, fname)
        try:
            os.remove(path)
            removed.append(path)
            print('Removed:', path)
        except Exception as e:
            print('Failed to remove', path, e)
    return removed
