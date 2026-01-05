import asyncio
import os
from urllib.parse import quote_plus

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


# ---------------- START ----------------

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    user = message.from_user
    text = templates.START_TEXT.format(
        first_name=user.first_name or "Friend"
    )
    await message.reply_text(
        text,
        reply_markup=keyboards.start_keyboard(
            join_username=config.ADMIN or "@MLinks"
        )
    )


# ---------------- PRIVATE CHANNEL FORWARD ----------------

@app.on_message(
    filters.chat(utils.parse_private_channel_list(config.PRIVATE_CHANNELS))
    & (filters.document | filters.video | filters.audio)
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

    if config.LOG_CHANNEL:
        try:
            await client.send_message(
                config.LOG_CHANNEL,
                f"Saved movie: {base_title} [{quality}] (key: {key})"
            )
        except:
            pass


# ---------------- TEXT SEARCH (MOVIE SEARCH) ----------------

@app.on_message(filters.text & ~filters.bot & ~filters.command)
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
        text=f"🔎 Results for: {query}",
        reply_markup=kb
    )


# ---------------- CALLBACK HANDLER ----------------

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data or ""
    user_id = callback_query.from_user.id

    # Pagination
    if data.startswith("page:"):
        page = int(data.split(":")[1])
        results = SEARCH_CACHE.get(user_id, [])
        items, total = utils.split_into_buttons(results, page)
        kb = keyboards.search_results_keyboard(items, page, total)
        await callback_query.edit_message_reply_markup(reply_markup=kb)
        await callback_query.answer()
        return

    # Movie clicked
    if data.startswith("movie:"):
        movie_id = int(data.split(":")[1])
        details = await tmdb.get_movie_details(movie_id, config.TMDB_API_KEY)

        if not details:
            await callback_query.answer("Details not found", show_alert=True)
            return

        title = details.get("title", "Unknown Movie")
        language = details.get("language", "N/A").upper()
        year = details.get("year", "N/A")
        rating = details.get("rating", "N/A")
        genres = ", ".join(details.get("genres", [])) or "N/A"

        caption = (
            f"{title}\n\n"
            f"🎬 Language : {language}\n"
            f"📅 Release : {year}\n"
            f"⭐ Rating  : {rating}\n"
            f"🎭 Genre   : {genres}"
        )

        # WATCH NOW → website search by movie name only
        search_query = quote_plus(title)
        watch_url = f"{config.WEBSITE}?search={search_query}"

        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "▶️ WATCH NOW",
                        url=watch_url
                    )
                ]
            ]
        )

        if details.get("poster"):
            await callback_query.message.reply_photo(
                photo=details["poster"],
                caption=caption,
                reply_markup=kb
            )
        else:
            await callback_query.message.reply_text(
                caption,
                reply_markup=kb
            )

        await callback_query.answer()
        return


# ---------------- ADMIN ----------------

@app.on_message(filters.command("admin") & filters.user(config.ADMIN))
async def admin_panel(client, message):
    text = (
        "Admin Commands:\n"
        "/stats - bot stats\n"
        "/shutdown - stop bot"
    )
    await message.reply_text(text)


@app.on_message(filters.command("stats"))
async def stats_cmd(client, message):
    text = (
        "📊 Bot Stats\n\n"
        f"Users cached searches: {len(SEARCH_CACHE)}\n"
        f"Website: {config.WEBSITE}"
    )
    await message.reply_text(text)


# ---------------- RUN ----------------

app.run()
