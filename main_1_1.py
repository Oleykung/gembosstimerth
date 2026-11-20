
import os
import threading
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Start web in thread
def start_web():
    try:
        from web import app
        port = int(os.getenv("WEB_PORT", "5000"))
        print(f"🌐 Web Server starting http://localhost:{port}")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Web error: {e}")

if __name__ == "__main__":
    # Start web thread
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()

    # Start bot (this blocks)
    import bot
    import discord
    from bot import client, DISCORD_TOKEN
    if not DISCORD_TOKEN or "ใส่โทเคน" in DISCORD_TOKEN:
        print("❌ กรุณาใส่ DISCORD_TOKEN ในไฟล์ .env ก่อน")
        print("ดูวิธีทำใน README.md")
        exit(1)
    
    # Run bot
    client.run(DISCORD_TOKEN)
