# keyboards.py
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_keyboard(join_username: str = "@M2LiNKS"):
    kb = [
        [InlineKeyboardButton("➕ ADD ME TO YOUR GROUP ➕", url=f"https://t.me/{join_username.strip('@')}?startgroup=true")],
        [
            InlineKeyboardButton("BACKUP CHANNEL", url="https://t.me/your_backup_channel"),
            InlineKeyboardButton("BOTS CHANNEL", url="https://t.me/your_bots_channel")
        ],
        [
            InlineKeyboardButton("MOVIES GROUP", url="https://t.me/your_movies_group"),
            InlineKeyboardButton("OFFERS CHANNEL", url="https://t.me/your_offers_channel")
        ],
        [InlineKeyboardButton("SHARE ME", switch_inline_query="")]
    ]
    return InlineKeyboardMarkup(kb)

def search_results_keyboard(items: list, page: int, total_pages: int):
    kb = []
    for label, cb in items:
        kb.append([InlineKeyboardButton(label, callback_data=cb)])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️ PREV", callback_data=f"page:{page-1}"))
    nav.append(InlineKeyboardButton(f"PAGE {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("NEXT ➡️", callback_data=f"page:{page+1}"))
    kb.append(nav)
    return InlineKeyboardMarkup(kb)

def movie_detail_keyboard(movie_id: int, website: str, qualities: list = None, is_private: bool = False, join_username: str = "@M2LiNKS"):
    kb = []
    if qualities:
        # qualities is list of dicts: {'label': '1080p', 'cb': 'watch:...'}
        row = []
        for q in qualities:
            kb.append([InlineKeyboardButton(q['label'], callback_data=q['cb'])])
    if is_private:
        kb.append([
            InlineKeyboardButton("📥 COPY TO CHANNEL", callback_data=f"copy:{movie_id}"),
            InlineKeyboardButton("🔐 PRIVATE CHANNEL", url="https://t.me/your_private_channel")
        ])
    kb.append([InlineKeyboardButton("🔗 Join Us", url=f"https://t.me/{join_username.strip('@')}")])
    kb.append([InlineKeyboardButton("▶️ WATCH NOW", url=website)])
    return InlineKeyboardMarkup(kb)

def not_found_keyboard():
    kb = [[InlineKeyboardButton("🔎 Google Search", url="https://www.google.com/")]]
    return InlineKeyboardMarkup(kb)
