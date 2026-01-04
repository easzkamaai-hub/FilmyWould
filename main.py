import os
import threading
import asyncio
from aiohttp import web
from bot import app as tg_app


async def _start_dummy_server():
    port = int(os.environ.get("PORT", "8000"))

    async def handle(request):
        return web.Response(text="OK")

    web_app = web.Application()
    web_app.add_routes([web.get("/", handle)])

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Dummy HTTP server started on 0.0.0.0:{port}")

    # Keep the server running forever (until the process exits)
    await asyncio.Event().wait()


def _run_server_in_thread():
    try:
        asyncio.run(_start_dummy_server())
    except Exception as e:
        # If the server fails to start, log and continue — the main app will still run.
        print("Dummy server exited with error:", e)


if __name__ == "__main__":
    # Start the aiohttp server in a background (daemon) thread so Render can detect an open port
    server_thread = threading.Thread(target=_run_server_in_thread, daemon=True)
    server_thread.start()

    # Run the existing bot application (pyrogram)
    tg_app.run()
