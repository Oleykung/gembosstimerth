import json
import threading
from pathlib import Path
from datetime import datetime, timezone, timedelta
import os

BASE_DIR = Path(__file__).parent
BOSSES_FILE = BASE_DIR / "bosses.json"
TIMERS_FILE = BASE_DIR / "boss_timers.json"

ICT = timezone(timedelta(hours=int(os.getenv("TIMEZONE_OFFSET", "7"))))

_lock = threading.Lock()
_bot_client = None  # จะถูก set โดย bot.py ตอน on_ready
_channel_id = None

def set_bot_client(client, channel_id):
    global _bot_client, _channel_id
    _bot_client = client
    _channel_id = channel_id
    print(f"[SHARED] Bot client linked - Channel {channel_id}")

def get_bot_client():
    return _bot_client, _channel_id

def load_bosses():
    with open(BOSSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_timers():
    with _lock:
        if TIMERS_FILE.exists():
            try:
                with open(TIMERS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except:
                return {}
        return {}

def save_timers(data):
    with _lock:
        with open(TIMERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def set_boss_death(boss_id, respawn_hours, source="discord"):
    """ตั้งว่าบอสตาย - ใช้ร่วมกันทั้งเว็บและบอท"""
    bosses = load_bosses()
    bmap = {b["id"]: b for b in bosses}
    if boss_id not in bmap:
        return None
    b = bmap[boss_id]
    rh = respawn_hours or b.get("respawn_hours", 4)
    now = datetime.now(ICT)
    next_spawn = now + timedelta(hours=rh)

    timers = load_timers()
    timers[boss_id] = {
        "last_death": now.isoformat(),
        "next_spawn": next_spawn.isoformat(),
        "notified_10min": False,
        "notified_spawn": False,
        "last_source": source  # บอกว่าตายจากไหน เว็บหรือดิส
    }
    save_timers(timers)
    print(f"[SHARED] {b['name_th']} ตายโดย {source} -> เกิดใหม่ {next_spawn.strftime('%H:%M')}")
    return {"boss": b, "next_spawn": next_spawn, "now": now}

def reset_all_bosses(source="discord"):
    bosses = load_bosses()
    now = datetime.now(ICT)
    timers = {}
    for b in bosses:
        next_spawn = now + timedelta(hours=b.get("respawn_hours", 4))
        timers[b["id"]] = {
            "last_death": now.isoformat(),
            "next_spawn": next_spawn.isoformat(),
            "notified_10min": False,
            "notified_spawn": False,
            "last_source": source
        }
    save_timers(timers)
    print(f"[SHARED] Reset all 12 by {source}")
    return timers

def reset_city_bosses(city_key, source="discord"):
    bosses = load_bosses()
    now = datetime.now(ICT)
    timers = load_timers()
    count = 0
    for b in bosses:
        if b["city_key"] == city_key:
            next_spawn = now + timedelta(hours=b.get("respawn_hours", 4))
            timers[b["id"]] = {
                "last_death": now.isoformat(),
                "next_spawn": next_spawn.isoformat(),
                "notified_10min": False,
                "notified_spawn": False,
                "last_source": source
            }
            count += 1
    save_timers(timers)
    print(f"[SHARED] Reset city {city_key} {count} ตัว by {source}")
    return count
