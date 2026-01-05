import asyncio
import os

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config, tmdb, keyboards, templates, utils, storage


app = Client(
    "FilmyWould",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

SEARCH_CACHE = {}


# ------------------ ADMIN CHECK ------------------
def is_admin(user_id: int) -> bool:
    try:
        admins = [int(x) for x in (config.ADMIN or "").split() if x.isdigit()]
        return user_id in admins
    except:
        return False


# ------------------ PRIVATE CHANNEL LIST ------------------
def parse_private_channel_list():
    raw = config.PRIVATE_CHANNELS or ""
    items = [x.strip() for x in raw.split(",") if x.strip()]
    out = []
    for it in items:
        try:
            out.append(int(it))
        except:
            out.append(it)
    return out


PRIVATE_LIST = parse_private_channel_list()


# ------------------ START ------------------
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    user = message.from_user
    caption = templates.START_TEXT.format(
        first_name=user.first_name or "Friend"
    )

    await message.reply_text(
        caption,
        reply_markup=keyboards.start_keyboard()
    )


# ------------------ PRIVATE CHANNEL FORWARD ------------------
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

    if config.BACKUP_CHANNEL:
        try:
            await client.copy_message(
                chat_id=config.BACKUP_CHANNEL,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
        except:
            pass

    if config.LOG_CHANNEL:
        try:
            await client.send_message(
                config.LOG_CHANNEL,
                f"Saved movie: {base_title} [{quality}] (key: {key})"
            )
        except:
            pass


# ------------------ TEXT SEARCH (FIXED) ------------------
@app.on_message(filters.text & ~filters.command & ~filters.bot)
async def text_search_handler(client, message):
    query = message.text.strip()
    user_id = message.from_user.id
    results = []

    data = await tmdb.search_tmdb(query, config.TMDB_API_KEY, page=1)

    if data and data.get("results"):
        for r in data["results"][:50]:
            label = f"{r.get('title')} ({(r.get('release_date') or '')[:4]})"
            results.append({
                "id": r["id"],
                "label": label
            })

        SEARCH_CACHE[user_id] = results
        items, total = utils.split_into_buttons(results, page=1)

        kb = keyboards.search_results_keyboard(items, 1, total)

        await client.send_message(
            chat_id=message.chat.id,
            text=templates.SEARCH_HEADER + f"Results for : {query}",
            reply_markup=kb
        )
    else:
        await message.reply_text(
            templates.NOT_FOUND_TEXT,
            reply_markup=keyboards.not_found_keyboard()
        )


# ------------------ CALLBACKS ------------------
@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data or ""
    user_id = callback_query.from_user.id

    # ---------- PAGINATION ----------
    if data.startswith("page:"):
        page = int(data.split(":")[1])
        results = SEARCH_CACHE.get(user_id, [])
        items, total = utils.split_into_buttons(results, page=page)
        kb = keyboards.search_results_keyboard(items, page, total)

        await callback_query.edit_message_reply_markup(reply_markup=kb)
        await callback_query.answer()
        return

    # ---------- MOVIE DETAILS ----------
    if data.startswith("movie:"):
        movie_id = int(data.split(":")[1])
        details = await tmdb.get_movie_details(movie_id, config.TMDB_API_KEY)

        if not details:
            await callback_query.answer("Details not found", show_alert=True)
            return

        key = utils.slugify(details.get("title") or "")
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

        caption = (
            f"<b>{details.get('title')}</b>\n"
            f"{(details.get('original_language') or '').upper()} • "
            f"{details.get('release_date','')[:4]} • "
            f"⭐ {details.get('vote_average','N/A')}\n\n"
            f"🎭 {', '.join([g['name'] for g in details.get('genres', [])])}"
        )

        kb = keyboards.movie_detail_keyboard(
            movie_id=movie_id,
            website=f"{config.WEBSITE}?s={details.get('title','').replace(' ', '+')}",
            qualities=qualities,
            is_private=is_private
        )

        if details.get("poster"):
            await callback_query.message.reply_photo(
                details["poster"],
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
        else:
            await callback_query.message.reply_text(
                caption,
                reply_markup=kb,
                parse_mode="HTML"
            )

        await callback_query.answer()
        return

    # ---------- WATCH ----------
    if data.startswith("watch:"):
        parts = data.split(":")
        if len(parts) != 3:
            await callback_query.answer()
            return

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
            await callback_query.answer("Here is your movie")
        except:
            await callback_query.answer(
                "Failed to fetch. Contact admin.",
                show_alert=True
            )
        return


# ------------------ ADMIN PANEL ------------------
@app.on_message(filters.command("admin"))
async def admin_panel(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("❌ You are not admin.")

    text = (
        "🛠 Admin Commands\n\n"
        "/stats - Bot stats\n"
    )
    await message.reply_text(text)


# ------------------ STATS (FIXED) ------------------
@app.on_message(filters.command("stats"))
async def stats_cmd(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("❌ You are not admin.")

    text = (
        "📊 Bot Stats\n\n"
        f"Cached searches: {len(SEARCH_CACHE)}\n"
        f"Website: {config.WEBSITE}"
    )
    await message.reply_text(text)


# ------------------ RUN ------------------
app.run()
