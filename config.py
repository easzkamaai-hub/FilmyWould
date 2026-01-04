# config.py
import os
from typing import List

# Read env vars safely (no hardcoded numbers)
def _int_env(name: str, default: int = 0) -> int:
    val = os.environ.get(name, "")
    try:
        return int(val) if val != "" else default
    except Exception:
        return default

API_ID = _int_env("API_ID", 0)
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# TMDB and site
TMDB_API_KEY = os.environ.get("TMDB", "")  # TMDB API key
WEBSITE = os.environ.get("WEBSITE", "https://example.com")

# Admins / channels (strings). ADMIN may be comma-separated user ids or usernames
ADMIN = os.environ.get("ADMIN", "")
CHANNELS = os.environ.get("CHANNELS", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
LOG_CHANNEL = os.environ.get("LOG_CHANNEL", "")

# Private channels where you forward movies — comma separated chat ids or @usernames
PRIVATE_CHANNELS = os.environ.get("PRIVATE_CHANNELS", "")
# Backup channel where bot may copy messages
BACKUP_CHANNEL = os.environ.get("BACKUP_CHANNEL", "")

# Helpers
def parse_admin_ids(admin_raw: str) -> List[int]:
    ids: List[int] = []
    for part in (admin_raw or "").split(','):
        p = part.strip()
        if not p:
            continue
        try:
            ids.append(int(p))
        except Exception:
            # skip non-numeric (usernames)
            continue
    return ids

ADMIN_IDS = parse_admin_ids(ADMIN)

# Debug helper (do not print tokens in production)
def env_summary() -> dict:
    return {
        'API_ID': API_ID,
        'API_HASH_set': bool(API_HASH),
        'BOT_TOKEN_set': bool(BOT_TOKEN),
        'TMDB_set': bool(TMDB_API_KEY),
        'ADMIN_ids': ADMIN_IDS,
        'PRIVATE_CHANNELS': PRIVATE_CHANNELS,
    }
