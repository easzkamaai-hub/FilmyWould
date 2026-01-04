# storage.py
import json
from pathlib import Path
from threading import Lock
from typing import Dict, Any

STORE_PATH = Path('data')
STORE_FILE = STORE_PATH / 'movies.json'
lock = Lock()

def _ensure():
    STORE_PATH.mkdir(parents=True, exist_ok=True)
    if not STORE_FILE.exists():
        STORE_FILE.write_text(json.dumps({}))

def load_all() -> Dict[str, Any]:
    _ensure()
    with lock:
        return json.loads(STORE_FILE.read_text())

def save_all(data: Dict[str, Any]):
    _ensure()
    with lock:
        STORE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def add_quality(movie_key: str, movie_title: str, quality: str, chat_id: int, message_id: int):
    data = load_all()
    if movie_key not in data:
        data[movie_key] = {"title": movie_title, "qualities": []}
    # avoid duplicates for same quality
    exists = False
    for q in data[movie_key]['qualities']:
        if q['quality'] == quality:
            exists = True
            # update message reference
            q.update({"chat_id": chat_id, "message_id": message_id})
            break
    if not exists:
        data[movie_key]['qualities'].append({"quality": quality, "chat_id": chat_id, "message_id": message_id})
    # keep at most 5 qualities
    data[movie_key]['qualities'] = data[movie_key]['qualities'][:5]
    save_all(data)

def get_movie(movie_key: str):
    data = load_all()
    return data.get(movie_key)
