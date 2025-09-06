"""
Helpers to read/write the .env file using python-dotenv.
"""
import os
from dotenv import load_dotenv, set_key, find_dotenv

# Find or create .env path
ENV_PATH = find_dotenv() or os.path.join(os.getcwd(), '.env')
load_dotenv(ENV_PATH)


def ensure_env_file(path):
    """Create an empty .env if it does not exist and reload environment."""
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write('')
    load_dotenv(path)
    return path


def save_to_env(key, value, env_path_local=None):
    """Save key=value into the specified .env file and reload env vars."""
    path = env_path_local or ENV_PATH
    ensure_env_file(path)
    set_key(path, key, value)
    load_dotenv(path)


def remove_env_key(key, env_path_local=None):
    """Remove a key from the .env file (line-based) and reload env vars."""
    path = env_path_local or ENV_PATH
    if not os.path.exists(path):
        return False
    kept = []
    removed = False
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith(f"{key}="):
                removed = True
                continue
            kept.append(line)
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(kept)
    load_dotenv(path)
    return removed
