# tmdb.py
import aiohttp
from urllib.parse import urlencode

TMDB_API = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

async def search_tmdb(query: str, api_key: str, page: int = 1):
    q = {"api_key": api_key, "query": query, "page": page, "include_adult": False}
    url = f"{TMDB_API}/search/movie?{urlencode(q)}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=15) as r:
            if r.status == 200:
                return await r.json()
            return None

async def get_movie_details(movie_id: int, api_key: str):
    params = {"api_key": api_key, "append_to_response": "credits"}
    url = f"{TMDB_API}/movie/{movie_id}?{urlencode(params)}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                poster = IMAGE_BASE + data.get("poster_path") if data.get("poster_path") else None
                title = data.get("title")
                year = (data.get("release_date") or "")[:4]
                language = data.get("original_language")
                rating = data.get("vote_average")
                genres = ", ".join([g["name"] for g in data.get("genres", [])])
                return {
                    "poster": poster,
                    "title": title,
                    "year": year,
                    "language": language,
                    "rating": rating,
                    "genres": genres,
                    "overview": data.get("overview", "")
                }
            return None
