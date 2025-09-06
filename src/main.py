#!/usr/bin/env python3
"""
CLI entrypoint. It wires together env, auth, token refresh and calls export_json. Provides --plain-files which writes plain text files (playlist_<id>.txt) next to each JSON export
Also provides --purge, --purge-all, --delete-owner, --disconnect and --clear-env utilities to manage stored exports and env.
"""
import os
import sys
import argparse
from dotenv import load_dotenv

from env_utils import save_to_env, ENV_PATH, ensure_env_file, remove_env_key
from auth import authorization_code_flow, refresh_token_flow
from export_json import export_playlists_and_tracks
from purge_utils import purge_expired_exports, delete_exports_for_owner, purge_all_exports

# Load environment
load_dotenv()


def confirm_prompt(message):
    try:
        resp = input(f"{message} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return resp in ('y', 'yes')


def main():
    parser = argparse.ArgumentParser(description='Export Spotify playlists to JSON (uses .env)')
    parser.add_argument('--out', default='exports', help='Output directory for per-playlist JSON files')
    parser.add_argument('--all', action='store_true', help='Export all playlists without prompt')
    parser.add_argument('--no-save-refresh', action='store_true',
                        help="Do NOT save the refresh token to the .env if received")
    parser.add_argument('--env', help='Path to .env (optional)')
    parser.add_argument('--purge', action='store_true', help='Purge expired exports in the output directory and exit')
    parser.add_argument('--purge-all', action='store_true',
                        help='Force-delete ALL export JSON files in the output directory (confirmation required unless --yes)')
    parser.add_argument('--delete-owner', help='Delete exports for the given owner_id (owner Spotify user id) and exit')
    parser.add_argument('--disconnect', action='store_true',
                        help='Remove saved SPOTIFY_REFRESH_TOKEN from .env (disconnect)')
    parser.add_argument('--clear-env', action='store_true', help='Clear the .env file (truncate). Use with caution.')
    parser.add_argument('--yes', action='store_true', help='Answer yes to confirmation prompts')
    parser.add_argument('--ttl-days', type=int, default=int(os.environ.get('EXPORT_TTL_DAYS', '2')),
                        help='Number of days to keep exported files (default from ENV or 2)')
    parser.add_argument('--plain-files', action='store_true',
                        help='Also write plain text files next to the JSON exports')

    args = parser.parse_args()

    env_path = args.env or ENV_PATH
    ensure_env_file(env_path)

    # Purge expired or delete-owner or purge-all or clear-env or disconnect
    if args.purge:
        removed = purge_expired_exports(args.out)
        print(f"Removed {len(removed)} files.")
        sys.exit(0)

    if args.delete_owner:
        deleted = delete_exports_for_owner(args.out, args.delete_owner)
        print(f"Deleted {len(deleted)} files for owner {args.delete_owner}.")
        sys.exit(0)

    if args.purge_all:
        if args.yes or confirm_prompt(f"This will permanently delete all JSON exports in '{args.out}'. Continue?"):
            removed = purge_all_exports(args.out)
            print(f"Force-removed {len(removed)} files.")
            sys.exit(0)
        else:
            print('Aborted purge-all.')
            sys.exit(1)

    if args.disconnect:
        if args.yes or confirm_prompt("Remove SPOTIFY_REFRESH_TOKEN from the .env file and disconnect? "):
            removed = remove_env_key('SPOTIFY_REFRESH_TOKEN', env_path_local=env_path)
            if removed:
                print('SPOTIFY_REFRESH_TOKEN removed from .env')
            else:
                print('No SPOTIFY_REFRESH_TOKEN found in .env')
            sys.exit(0)
        else:
            print('Disconnect aborted.')
            sys.exit(1)

    if args.clear_env:
        if args.yes or confirm_prompt(f"This will truncate/clear the file {env_path}. Continue?"):
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write('')
            print(f'{env_path} truncated (cleared).')
            sys.exit(0)
        else:
            print('Clear .env aborted.')
            sys.exit(1)

    # Normal export flow
    client_id = os.environ.get('SPOTIFY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.environ.get('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
    existing_refresh = os.environ.get('SPOTIFY_REFRESH_TOKEN')

    access_token = None

    if existing_refresh:
        if not client_id or not client_secret:
            print('SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are required in .env to refresh token.')
            sys.exit(1)
        print('Using refresh token from .env to request an access token...')
        token_data = refresh_token_flow(client_id, client_secret, existing_refresh)
        access_token = token_data.get('access_token')
    else:
        if not client_id or not client_secret:
            print('Please define SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env or environment variables.')
            sys.exit(1)
        token_data = authorization_code_flow(client_id, client_secret, redirect_uri)
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        if refresh_token and (not args.no_save_refresh):
            print('Saving refresh token into .env for future runs...')
            save_to_env('SPOTIFY_REFRESH_TOKEN', refresh_token, env_path_local=env_path)
            print(f'Refresh token written to {env_path} (protect this file!).')

    if not access_token:
        print('Unable to obtain access token. Check credentials and .env.')
        sys.exit(1)

    try:
        export_playlists_and_tracks(
            access_token,
            args.out,
            export_all=args.all,
            ttl_days=args.ttl_days,
            write_plain_files=bool(args.plain_files)
        )
    except Exception as e:
        print('Error:', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
