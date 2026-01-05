# bot.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config, tmdb, keyboards, templates, utils, storage
import os

app = Client("filmybot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

SEARCH_CACHE = {}

def parse_private_channel_list():
    raw = config.PRIVATE_CHANNELS or ""
    items = [x.strip() for x in raw.split(',') if x.strip()]
    # try convert numeric ids
    out = []
    for it in items:
        try:
            out.append(int(it))
        except:
            out.append(it)
    return out

PRIVATE_LIST = parse_private_channel_list()

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    user = message.from_user
    caption = templates.START_TEXT.format(first_name=user.first_name or "Friend")
    await message.reply_text(
        caption,
        reply_markup=keyboards.start_keyboard(join_username=config.ADMIN or "@MLinks")
    )

@app.on_message(filters.chat(PRIVATE_LIST) & (filters.document | filters.video | filters.audio | filters.photo))
async def private_channel_forwarded_handler(client, message):
    # triggered when a media message arrives in configured private channels
    # Try to extract title and quality
    caption = (message.caption or "").strip()
    filename = None
    if message.document and message.document.file_name:
        filename = message.document.file_name
    if message.video and getattr(message.video, 'file_name', None):
        filename = message.video.file_name
    source_text = caption or filename or ''
    # crude title: if caption contains dash or brackets, try first line
    first_line = source_text.split('\n')[0]
    # parse quality
    quality = utils.parse_quality_from_text(source_text)
    # derive base title by removing quality tokens
    base_title = first_line
    # create movie key
    key = utils.slugify(base_title)
    # store
    storage.add_quality(key, base_title, quality, message.chat.id, message.message_id)
    # optionally copy to backup channel if configured
    if config.BACKUP_CHANNEL:
        try:
            await client.copy_message(chat_id=config.BACKUP_CHANNEL, from_chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e:
            # ignore
            pass
    # log
    if config.LOG_CHANNEL:
        try:
            await client.send_message(config.LOG_CHANNEL, f"Saved movie: {base_title} [{quality}] (key: {key})")
        except:
            pass

@app.on_message(filters.text & ~filters.bot)
async def text_search_handler(client, message):
    query = message.text.strip()
    user_id = message.from_user.id
    results = []
    data = await tmdb.search_tmdb(query, config.TMDB_API_KEY, page=1)
    if data and data.get("results"):
    for r in data["results"][:50]:
        label = f"{r.get('title')} ({(r.get('release_date') or '')[:4]})"
        results.append({"id": r["id"], "label": label})

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
@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data or ""
    user_id = callback_query.from_user.id

    if data.startswith("page:"):
        page = int(data.split(":")[1])
        results = SEARCH_CACHE.get(user_id, [])
        items, total = utils.split_into_buttons(results, page=page)
        kb = keyboards.search_results_keyboard(items, page, total)
        await callback_query.edit_message_reply_markup(reply_markup=kb)
        await callback_query.answer()
        return

    if data.startswith("movie:"):
        movie_id = int(data.split(":")[1])
        details = await tmdb.get_movie_details(movie_id, config.TMDB_API_KEY)
        if not details:
            await callback_query.answer("Details not found", show_alert=True)
            return
        # check local storage for saved qualities using title slug
        key = utils.slugify(details.get('title') or '')
        local = storage.get_movie(key)
        qualities = None
        is_private = False
        if local and local.get('qualities'):
            qualities = []
            for idx, q in enumerate(local['qualities']):
                qualities.append({'label': q['quality'], 'cb': f"watch:{key}:{idx}"})
            is_private = True
        caption = f"<b>{details['title']}</b>\n{(details['language'] or '').upper()} • {details['year']} • ⭐ {details['rating']} \nGenres: {details['genres']}\n\n{details['overview']}\n\nJoin Us : {config.ADMIN or '@M2LiNKS'}"
        kb = keyboards.movie_detail_keyboard(movie_id, website=config.WEBSITE, qualities=qualities, is_private=is_private, join_username=config.ADMIN or "@M2LiNKS")
if details.get("poster"):
    await callback_query.message.reply_photo(
        details["poster"],
        caption=caption,
        reply_markup=kb,
        parse_mode="HTML"
    )
else:
    await callback_query.message.reply_photo(
        photo=details["backdrop"],
        caption=caption,
        reply_markup=kb,
        parse_mode="HTML"
    )
        await callback_query.answer()
        return

    if data.startswith("watch:"):
        # watch:key:idx
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
        q = movie['qualities'][idx]
        # copy the saved message to user's chat
        try:
            await client.copy_message(chat_id=callback_query.message.chat.id, from_chat_id=q['chat_id'], message_id=q['message_id'])
            await callback_query.answer("Here is your requested quality")
        except Exception as e:
            await callback_query.answer("Failed to fetch. Contact admin.", show_alert=True)
        return

    if data.startswith("copy:"):
        admin_ids = [int(x) for x in (config.ADMIN or "").split(",") if x.strip().isdigit()]
        if callback_query.from_user.id not in admin_ids:
            await callback_query.answer(templates.NOT_ADMIN_BREACH, show_alert=True)
            return
        movie_id = int(data.split(":")[1])
        await callback_query.answer("Copying movie to your channel...", show_alert=False)
        return

@app.on_message(filters.command("admin") & filters.user(int(config.ADMIN) if config.ADMIN.isdigit() else None))
async def admin_panel(client, message):
    text = "Admin Commands:\n• /stats - bot stats\n• /channels - configured channels\n• /broadcast <text> - broadcast\n• /shutdown - stop bot"
    await message.reply_text(text)

@app.on_message(filters.command("status"))
async def status_cmd(client, message):
    text = f"Bot State:\nUsers cached searches: {len(SEARCH_CACHE)}\nWebsite: {config.WEBSITE}"
    await message.reply_text(text)

if __name__ == "__main__":
    print("Starting FilmyWould bot...")
    app.run()
