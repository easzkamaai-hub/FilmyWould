# FilmyWould — Telegram Bot templates & starter

यह प्रोजेक्ट Pyrogram-based starter है जो आपने जो screenshots भेजे थे वैसा UI/UX replicate करने के लिए बनाया गया है।

मुख्य features:
- start message (photo1) with tiles/buttons
- search by user text -> TMDB search -> paginated results (photo2 style)
- movie detail view with poster, title, language, year, rating, genres, Join Us + Watch Now (photo3)
- not found flow with special font message and Google Search button (photo4)
- admin commands and bot state command
- private-channel auto-save: when you forward media in configured private channels the bot will save up to multiple qualities under a single movie key

Required env vars:
- BOT_TOKEN
- API_ID
- API_HASH
- TMDB (TMDB API key)
- WEBSITE (link for WATCH NOW)
- ADMIN (admin id or comma-separated ids)
- PRIVATE_CHANNELS (comma-separated chat ids or usernames where you forward movies)
- BACKUP_CHANNEL (optional) - where messages are copied
- LOG_CHANNEL (optional) - where internal logs are sent

Assets:
- assets/photo1.jpg
- assets/photo2.jpg
- assets/photo3.jpg
- assets/photo4.jpg

Run:
1. pip install pyrogram tgcrypto aiohttp
2. export the required env vars
3. python bot.py

Customization:
- Replace URLs in keyboards.py with your channels and links
- Implement DB-backed storage for production if needed (currently uses JSON file in data/movies.json)
- Improve UI fonts/formatting — HTML parse_mode used for details
