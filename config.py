# config.py
import os

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
TMDB_API_KEY = os.environ.get("TMDB", "")  # TMDB API key
WEBSITE = os.environ.get("WEBSITE", "https://example.com")
ADMIN = os.environ.get("ADMIN", "")        # admin id(s) comma separated or username
CHANNELS = os.environ.get("CHANNELS", "")  # other channels (comma separated)
DATABASE_URL = os.environ.get("DATABASE_URL", "")
LOG_CHANNEL = os.environ.get("LOG_CHANNEL", "")
# Private channels where you forward movies — comma separated chat ids or @usernames
PRIVATE_CHANNELS = os.environ.get("PRIVATE_CHANNELS", "")
# Backup channel where bot may copy messages
BACKUP_CHANNEL = os.environ.get("BACKUP_CHANNEL", "")
