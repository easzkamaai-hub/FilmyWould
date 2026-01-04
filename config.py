# config.py
import os

API_ID = int(os.environ.get("26576868")
API_HASH = os.environ.get("7c091067324e2f3c6c7cdf8e575af4c8")
BOT_TOKEN = os.environ.get("7754868963:AAFikhhRpVsDA--LYVOVpONiglPC9Ai7Lek")
TMDB_API_KEY = os.environ.get("03985d11f17343d76561cebc240f5a32")  # TMDB API key
WEBSITE = os.environ.get("https://www.filmyfiy.mov/site-1.html?to-search=", "https://example.com")
ADMIN = os.environ.get("6328021097")        # admin id(s) comma separated or username
CHANNELS = os.environ.get("-1003618747014")  # other channels (comma separated)
DATABASE_URL = os.environ.get("mongodb+srv://<db_username>:pusparaj1@pusparaj.klkgcoz.mongodb.net/?appName=Pusparaj")
LOG_CHANNEL = os.environ.get("-1003692212713")
# Private channels where you forward movies — comma separated chat ids or @usernames
PRIVATE_CHANNELS = os.environ.get("-1003550652957")
# Backup channel where bot may copy messages
BACKUP_CHANNEL = os.environ.get("-1003300889716")
