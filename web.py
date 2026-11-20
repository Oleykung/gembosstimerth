
from flask import Flask, jsonify, render_template_string, request
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", "7"))
ICT = timezone(timedelta(hours=TIMEZONE_OFFSET))

BASE_DIR = Path(__file__).parent
BOSSES_FILE = BASE_DIR / "bosses.json"
TIMERS_FILE = BASE_DIR / "boss_timers.json"

app = Flask(__name__)

def load_bosses():
    with open(BOSSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_timers():
    if TIMERS_FILE.exists():
        with open(TIMERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Granado Espada M - Boss Timer TH</title>
<style>
body { background:#0f0f0f; color:#eee; font-family: 'Kanit', sans-serif; padding:20px; }
h1 { color:#fff; }
.card { background:#1e1e1e; border-radius:12px; padding:16px; margin:12px 0; border-left:6px solid #ff0000; }
.th { color:#ff4444; font-size:1.6em; font-weight:800; } /* ไทยแดง */
.en { color:#ffeb3b; font-size:1.0em; font-weight:400; } /* อังกฤษเหลือง */
.map-th { color:#ff8888; } 
.map-en { color:#ffe082; }
.city { font-size:0.9em; color:#aaa; }
.timer { font-size:1.2em; margin-top:8px; }
button { background:#ff0000; color:white; border:none; padding:8px 14px; border-radius:8px; cursor:pointer; margin-top:8px; }
button:hover { background:#cc0000; }
.filter { margin:10px 0; }
.filter button { background:#333; margin-right:6px; }
.filter button.active { background:#ff0000; }
#clock { font-size:1.2em; color:#0f0; }
</style>
</head>
<body>
<h1>Granado Espada M - บอส 12 ตัว เซิร์ฟไทย</h1>
<div id="clock"></div>
<div class="filter">
<button class="active" onclick="filterCity('all')">ทั้งหมด</button>
<button onclick="filterCity('reboldoeux')">รีโบลโดซ์ Reboldoeux</button>
<button onclick="filterCity('coimbra')">คอยมบรา Coimbra</button>
<button onclick="filterCity('auch')">อูช Auch</button>
</div>
<div style="background:#2a0000; border:2px solid #ff0000; border-radius:12px; padding:14px; margin:16px 0;">
  <div style="font-size:1.1em; font-weight:800; color:#fff; margin-bottom:10px;">🔄 RESET บอส</div>
  <button onclick="resetAll()" style="background:#ff0000; font-size:1.1em; padding:12px 20px; font-weight:800; border:none; border-radius:8px; color:white; cursor:pointer;">🔄 RESET บอสทุกตัว (12 ตัว)</button>
  <div style="margin-top:10px;">
    <button onclick="resetCity('reboldoeux')" style="background:#ff6600; border:none; padding:8px 12px; border-radius:8px; color:white; cursor:pointer;">Reset Reboldoeux (4 ตัว)</button>
    <button onclick="resetCity('coimbra')" style="background:#ffaa00; border:none; padding:8px 12px; border-radius:8px; cursor:pointer;">Reset Coimbra (4 ตัว)</button>
    <button onclick="resetCity('auch')" style="background:#aa00ff; border:none; padding:8px 12px; border-radius:8px; color:white; cursor:pointer;">Reset Auch (4 ตัว)</button>
  </div>
  <div id="resetMsg" style="color:#0f0; margin-top:8px;"></div>
</div>
<div id="bossList"></div>

<script>
let bosses = [];
async function load() {
  const res = await fetch('/api/bosses');
  bosses = await res.json();
  render(bosses);
}
function render(list) {
  const container = document.getElementById('bossList');
  container.innerHTML = '';
  list.forEach(b => {
    const next = new Date(b.next_spawn);
    const now = new Date();
    const diff = next - now;
    let status = '';
    if (diff <= 0) status = '🔥 เกิดแล้ว!';
    else {
      const m = Math.floor(diff/60000);
      const h = Math.floor(m/60);
      const mm = m%60;
      status = `⏰ อีก ${h}ชม. ${mm}นาที`;
    }
    const div = document.createElement('div');
    div.className = 'card';
    div.dataset.city = b.city_key;
    div.innerHTML = `
      <div class="th">${b.name_th}</div>
      <div class="en">${b.name_en}</div>
      <div class="map-th">## แผนที่: ${b.map_th} | เมือง: ${b.city_th}</div>
      <div class="map-en">-# Map: ${b.map_en} | City: ${b.city_en}</div>
      <div class="timer">${status} - เกิดทุก ${b.respawn_hours}ชม. | Next: ${next.toLocaleString('th-TH')}</div>
      <button onclick="killBoss('${b.id}')">kill boss - แจ้งตาย</button>
    `;
    container.appendChild(div);
  });
}
async function resetAll() {
  if (!confirm('ยืนยัน RESET บอสทั้ง 12 ตัว ใช่ไหม? เวลาจะถูกตั้งใหม่ทั้งหมด')) return;
  const res = await fetch('/api/reset_all', {method:'POST'});
  const data = await res.json();
  document.getElementById('resetMsg').innerText = '✅ Reset บอสทั้ง 12 ตัวเรียบร้อย - ' + new Date().toLocaleString('th-TH');
  load();
}
async function resetCity(city) {
  const cityName = city==='reboldoeux'?'Reboldoeux': city==='coimbra'?'Coimbra':'Auch';
  if (!confirm('ยืนยัน RESET บอสเมือง '+cityName+' ทั้ง 4 ตัว ใช่ไหม?')) return;
  await fetch('/api/reset_city', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({city})});
  document.getElementById('resetMsg').innerText = '✅ Reset บอสเมือง '+cityName+' เรียบร้อย';
  load();
}
async function killBoss(id) {
  if (!confirm('ยืนยันว่าบอสตาย? จะรีเซ็ตเวลาใหม่')) return;
  await fetch('/api/kill', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})});
  load();
}
function filterCity(key) {
  document.querySelectorAll('.filter button').forEach(btn=>btn.classList.remove('active'));
  event.target.classList.add('active');
  if (key==='all') render(bosses);
  else render(bosses.filter(b=>b.city_key===key));
}
function tick() {
  document.getElementById('clock').innerText = 'เวลาไทย (ICT): ' + new Date().toLocaleString('th-TH', {timeZone:'Asia/Bangkok'});
}
setInterval(tick,1000);
setInterval(load,30000);
load(); tick();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/bosses")
def api_bosses():
    bosses = load_bosses()
    timers = load_timers()
    result = []
    for b in bosses:
        t = timers.get(b["id"], {})
        next_spawn = t.get("next_spawn")
        result.append({**b, **t, "next_spawn": next_spawn})
    # sort by next_spawn
    result.sort(key=lambda x: x.get("next_spawn") or "")
    return jsonify(result)

@app.route("/api/kill", methods=["POST"])
def api_kill():
    data = request.json
    bid = data.get("id")
    timers = load_timers()
    bosses = load_bosses()
    bmap = {bb["id"]: bb for bb in bosses}
    if bid not in bmap:
        return jsonify({"error":"not found"}), 404
    b = bmap[bid]
    now = datetime.now(ICT)
    from datetime import timedelta
    next_spawn = now + timedelta(hours=b.get("respawn_hours",4))
    timers[bid] = {
        "last_death": now.isoformat(),
        "next_spawn": next_spawn.isoformat(),
        "notified_10min": False,
        "notified_spawn": False
    }
    with open(TIMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(timers, f, ensure_ascii=False, indent=2)
    return jsonify({"ok":True, "next_spawn": next_spawn.isoformat()})


@app.route("/api/reset_all", methods=["POST"])
def api_reset_all():
    timers = load_timers()
    bosses = load_bosses()
    now = datetime.now(ICT)
    for b in bosses:
        next_spawn = now + timedelta(hours=b.get("respawn_hours",4))
        timers[b["id"]] = {
            "last_death": now.isoformat(),
            "next_spawn": next_spawn.isoformat(),
            "notified_10min": False,
            "notified_spawn": False
        }
    with open(TIMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(timers, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "message": "Reset บอสทั้ง 12 ตัวเรียบร้อย", "count": len(bosses)})

@app.route("/api/reset_city", methods=["POST"])
def api_reset_city():
    data = request.json
    city = data.get("city")
    timers = load_timers()
    bosses = load_bosses()
    now = datetime.now(ICT)
    count = 0
    for b in bosses:
        if b["city_key"] == city:
            next_spawn = now + timedelta(hours=b.get("respawn_hours",4))
            timers[b["id"]] = {
                "last_death": now.isoformat(),
                "next_spawn": next_spawn.isoformat(),
                "notified_10min": False,
                "notified_spawn": False
            }
            count += 1
    with open(TIMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(timers, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "city": city, "count": count})

if __name__ == "__main__":

    port = int(os.getenv("WEB_PORT", "5000"))
    print(f"Web running http://localhost:{port} - ไทยแดง เหลืองอังกฤษ - kill boss ได้")
    app.run(host="0.0.0.0", port=port, debug=False)
