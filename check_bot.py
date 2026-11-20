# check_bot.py - รันเพื่อเช็คว่าทำไมไม่แจ้งเตือน
import os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
print("=== CHECK BOT NOTIFY ===")
token = os.getenv("DISCORD_TOKEN")
cid = os.getenv("CHANNEL_ID")
gid = os.getenv("GUILD_ID")
print(f"1. DISCORD_TOKEN: {'✅ มี' if token and len(token)>20 else '❌ ไม่มี / สั้นไป'}")
print(f"2. CHANNEL_ID: {cid} {'✅ มี' if cid and cid!='0' else '❌ ไม่มี - ต้องเป็น ID ห้อง (คลิกขวาห้อง > Copy Channel ID) ไม่ใช่ ID เซิร์ฟ'}")
print(f"3. GUILD_ID: {gid}")
print(f"4. boss_timers.json:")
p = Path("boss_timers.json")
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))
    now = datetime.now(timezone(timedelta(hours=7)))
    for k,v in data.items():
        try:
            ns = datetime.fromisoformat(v.get("next_spawn",""))
            diff = int((ns-now).total_seconds())
            print(f"   - {k}: Next {ns.strftime('%d/%m %H:%M')} diff {diff//60} นาที notified_10min={v.get('notified_10min')} spawn={v.get('notified_spawn')}")
            if diff < -1800:
                print(f"     ⚠️ เวลานี้เลยมาแล้ว { -diff//60} นาที บอทจะไม่แจ้ง (ต้อง /reset_all)")
        except Exception as e:
            print(f"   - {k}: เวลาพัง {v}")
else:
    print("   ไม่มีไฟล์")
print("")
print("ถ้าขึ้น 'เลยมาแล้ว' ให้พิมพ์ในดิส /reset_all แล้ว /setboss ตั้งเวลาใหม่")
print("ถ้า CHANNEL_ID ผิด ให้ก๊อปใหม่: เปิด Discord > Settings > Advanced > Developer Mode ON > คลิกขวาห้อง > Copy Channel ID")
