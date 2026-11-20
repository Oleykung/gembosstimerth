import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

def start_web():
    try:
        from web import app
        port = int(os.getenv("WEB_PORT", "5000"))
        print(f"🌐 Web SYNC Server starting http://0.0.0.0:{port} - ซิงค์กับดิสแล้ว")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Web error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Start web thread first
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()
    time.sleep(1)

    # Start bot
    import bot
    from bot import client, DISCORD_TOKEN

    if not DISCORD_TOKEN or "ใส่โทเคน" in DISCORD_TOKEN:
        print("❌ กรุณาใส่ DISCORD_TOKEN ในไฟล์ .env ก่อน")
        exit(1)
    
    print("🔗 SYNC MODE: บอท+เว็บใช้ไฟล์เดียวกันผ่าน shared.py")
    print("   - กด Kill ในเว็บ -> บอทในดิสอัปเดต + แจ้งในดิสทันที")
    print("   - พิมพ์ /kill ในดิส -> เว็บอัปเดตทันที")
    print("   - Reset ที่ไหน อีกที่ก็รีเซ็ตด้วย")
    
    client.run(DISCORD_TOKEN)
