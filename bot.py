import asyncio

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote_plus

import config
import tmdb
import keyboards
import templates
import utils
import storage


app = Client(
    "FilmyWould",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

SEARCH_CACHE = {}


# ---------------- PRIVATE CHANNEL LIST ---------------- #

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


# ---------------- START ---------------- #

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


# ---------------- SAVE FROM PRIVATE CHANNEL ---------------- #

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
                f"Saved movie: {base_title} [{quality}] | key: {key}"
            )
        except:
            pass


# ---------------- TEXT SEARCH ---------------- #

@app.on_message(filters.text & ~filters.command & ~filters.bot)
async def text_search_handler(client, message):
    query = message.text.strip()
    user_id = message.from_user.id
    results = []

    data = await tmdb.search_tmdb(query, config.TMDB_API_KEY, page=1)

    if data and data.get("results"):
        for r in data["results"][:50]:
            title = r.get("title") or r.get("name")
            year = (r.get("release_date") or "")[:4]
            label = f"{title} ({year})" if year else title
            results.append({
                "id": r["id"],
                "label": label
            })

        SEARCH_CACHE[user_id] = results
        items, total = utils.split_into_buttons(results, page=1)
        kb = keyboards.search_results_keyboard(items, 1, total)

        await client.send_message(
            chat_id=message.chat.id,
            text=f"🔍 Results for: {query}",
            reply_markup=kb
        )
    else:
        await message.reply_text(
            templates.NOT_FOUND_TEXT,
            reply_markup=keyboards.not_found_keyboard()
        )


# ---------------- CALLBACK ---------------- #

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id

    # -------- PAGINATION -------- #
    if data.startswith("page:"):
        page = int(data.split(":")[1])
        results = SEARCH_CACHE.get(user_id, [])
        items, total = utils.split_into_buttons(results, page=page)
        kb = keyboards.search_results_keyboard(items, page, total)

        await callback_query.edit_message_reply_markup(reply_markup=kb)
        await callback_query.answer()
        return

    # -------- MOVIE DETAILS -------- #
    if data.startswith("movie:"):
        movie_id = int(data.split(":")[1])
        details = await tmdb.get_movie_details(movie_id, config.TMDB_API_KEY)

        if not details:
            await callback_query.answer("Details not found", show_alert=True)
            return

        title = details.get("title") or "Unknown"
        year = details.get("year") or ""
        language = (details.get("language") or "").upper()
        rating = details.get("rating") or "N/A"
        genres = ", ".join(details.get("genres", []))

        caption = (
            f"🎬 {title}\n"
            f"📅 Year: {year}\n"
            f"🌐 Language: {language}\n"
            f"⭐ Rating: {rating}\n"
            f"🎭 Genre: {genres}"
        )

        watch_url = f"{config.WEBSITE}?search={quote_plus(title)}"
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ WATCH NOW", url=watch_url)]]
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

    await callback_query.answer()


# ---------------- ADMIN PANEL ---------------- #

@app.on_message(filters.command("admin") & filters.user(int(config.ADMIN)))
async def admin_panel(client, message):
    text = (
        "👮 Admin Commands\n\n"
        "/stats - bot stats\n"
        "/shutdown - stop bot"
    )
    await message.reply_text(text)


@app.on_message(filters.command("stats") & filters.user(int(config.ADMIN)))
async def stats_cmd(client, message):
    text = (
        "📊 Bot Stats\n\n"
        f"Cached Searches: {len(SEARCH_CACHE)}\n"
        f"Website: {config.WEBSITE}"
    )
    await message.reply_text(text)


@app.on_message(filters.command("shutdown") & filters.user(int(config.ADMIN)))
async def shutdown_cmd(client, message):
    await message.reply_text("Bot shutting down...")
    await app.stop()


# ---------------- RUN ---------------- #

app.run()
