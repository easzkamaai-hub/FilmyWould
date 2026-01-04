# utils.py
from typing import List
import re

def split_into_buttons(results: List[dict], page: int, per_page: int = 8):
    start = (page-1)*per_page
    end = start + per_page
    page_items = results[start:end]
    items = []
    for r in page_items:
        cb = f"movie:{r['id']}"
        label = r["label"]
        items.append((label, cb))
    total_pages = (len(results) + per_page - 1) // per_page or 1
    return items, total_pages

def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "_", s).strip("_")
    return s

def parse_quality_from_text(text: str) -> str:
    # crude parser: look for 1080p/720p/480p or WEB-DL/HDTC/HEVC patterns
    if not text:
        return "unknown"
    txt = text.lower()
    for q in ['1080p', '720p', '480p']:
        if q in txt:
            return q
    # fallback: try to find 'hd' indicators
    if 'hd' in txt:
        return '720p'
    return 'sd'
