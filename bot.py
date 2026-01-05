import asyncio
import os

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config, tmdb, keyboards, templates, utils, storage

app = Client(
    "FilmyWorld",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

SEARCH_CACHE = {}

# -------------------- ADMIN LIST --------------------
def get_admins():
    raw = config.ADMIN or ""
    return [int(x) for x in raw.split() if x.isdigit()]

ADMIN_IDS = get_admins()

# -------------------- PRIVATE CHANNELS --------------------
def parse_private_channel_list():
    raw = config.PRIVATE_CHANNELS or ""
    out = []
    for x in raw.split():
        try:
            out.append(int(x))
        except:
            out.append(x)
    return out

PRIVATE_LIST = parse_private_channel_list()

# -------------------- START --------------------
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    caption = templates.START_TEXT.format(
        first_name=message.from_user.first_name or "Friend"
    )
    await message.reply_text(
        caption,
        reply_markup=keyboards.start_keyboard(
            join_username=config.ADMIN or "@MLinks"
        )
    )

# -------------------- PRIVATE CHANNEL FORWARD --------------------
@app.on_message(
    filters.chat(PRIVATE_LIST)
    & (filters.document | filters.video | filters.audio | filters.photo)
)
async def private_channel_forwarded_handler(client, message):

    caption = (message.caption or "").strip()
    filename = None

    if message.document and message.document.file_name:
        filename = message.document.file_name
    if message.video and getattr(message.video, "file_name", None):
        filename = message.video.file_name

    source_text = caption or filename or ""
    first_line = source_text.split("\n")[0]

    quality = utils.parse_quality_from_text(source_text)
    base_title = first_line
    key = utils.slugify(base_title)

    storage.add_quality(
        key,
        base_title,
        quality,
        message.chat.id,
        message.message_id
    )

# -------------------- SEARCH --------------------
@app.on_message(filters.text & ~filters.bot)
async def text_search_handler(client, message):
    query = message.text.strip()
    user_id = message.from_user.id

    data = await tmdb.search_tmdb(query, config.TMDB_API_KEY, page=1)

    if not data or not data.get("results"):
        await message.reply_text(
            templates.NOT_FOUND_TEXT,
            reply_markup=keyboards.not_found_keyboard()
        )
        return

    results = []
    for r in data["results"][:50]:
        year = (r.get("release_date") or "")[:4]
        label = f"{r.get('title')}" + (f" ({year})" if year else "")
        results.append({
            "id": r["id"],
            "label": label
        })

    SEARCH_CACHE[user_id] = results

    items, total = utils.split_into_buttons(results, page=1)
    kb = keyboards.search_results_keyboard(items, 1, total)

    await message.reply_text(
        f"🔍 Results for: **{query}**",
        reply_markup=kb
    )

# -------------------- CALLBACK --------------------
@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data or ""
    user_id = callback_query.from_user.id

    # Pagination
    if data.startswith("page:"):
        page = int(data.split(":")[1])
        results = SEARCH_CACHE.get(user_id, [])
        items, total = utils.split_into_buttons(results, page=page)
        kb = keyboards.search_results_keyboard(items, page, total)
        await callback_query.edit_message_reply_markup(reply_markup=kb)
        await callback_query.answer()
        return

    # Movie details
    if data.startswith("movie:"):
        movie_id = int(data.split(":")[1])
        details = await tmdb.get_movie_details(movie_id, config.TMDB_API_KEY)

        if not details:
            await callback_query.answer("Details not found", show_alert=True)
            return

        title = details.get("title") or "Movie"
        key = utils.slugify(title)
        local = storage.get_movie(key)

        qualities = None
        is_private = False

        if local and local.get("qualities"):
            qualities = []
            for idx, q in enumerate(local["qualities"]):
                qualities.append({
                    "label": q["quality"],
                    "cb": f"watch:{key}:{idx}"
                })
            is_private = True

        caption = f"🎬 **{title}**"

        kb = keyboards.movie_detail_keyboard(
            movie_id=movie_id,
            website=f"{config.WEBSITE}?s={title}",
            qualities=qualities,
            is_private=is_private
        )

        if details.get("poster"):
            await callback_query.message.reply_photo(
                details["poster"],
                caption=caption,
                reply_markup=kb,
                parse_mode="Markdown"
            )
        else:
            await callback_query.message.reply_text(
                caption,
                reply_markup=kb,
                parse_mode="Markdown"
            )

        await callback_query.answer()
        return

    # Watch
    if data.startswith("watch:"):
        parts = data.split(":")
        key = parts[1]
        idx = int(parts[2])

        movie = storage.get_movie(key)
        if not movie:
            await callback_query.answer("Not available", show_alert=True)
            return

        q = movie["qualities"][idx]

        try:
            await client.copy_message(
                chat_id=callback_query.message.chat.id,
                from_chat_id=q["chat_id"],
                message_id=q["message_id"]
            )
            await callback_query.answer("Here is your movie 🎥")
        except:
            await callback_query.answer("Failed to fetch", show_alert=True)

        return

# -------------------- ADMIN PANEL (FIXED) --------------------
@app.on_message(filters.command("admin") & filters.user(ADMIN_IDS))
async def admin_panel(client, message):
    text = (
        "👮 **Admin Commands**\n\n"
        "/stats - Bot stats\n"
        "/channels - configured channels\n"
        "/broadcast <text>\n"
        "/shutdown"
    )
    await message.reply_text(text)

@app.on_message(filters.command("stats") & filters.user(ADMIN_IDS))
async def stats_cmd(client, message):
    text = (
        "📊 **Bot Stats**\n\n"
        f"Cached Searches: {len(SEARCH_CACHE)}\n"
        f"Website: {config.WEBSITE}"
    )
    await message.reply_text(text)

# -------------------- RUN --------------------
app.run()
