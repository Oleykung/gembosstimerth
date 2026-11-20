from flask import Flask, jsonify, render_template_string, request
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", "7"))
ICT = timezone(timedelta(hours=TIMEZONE_OFFSET))

BASE_DIR = Path(__file__).parent
BOSSES_FILE = BASE_DIR / "bosses.json"

# ใช้ shared เป็นตัวกลาง
import shared

app = Flask(__name__)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gem Boss Timer TH - Sync Discord + Website</title>
<style>
body { background:#0f0f0f; color:#eee; font-family: 'Kanit', sans-serif; padding:20px; }
h1 { color:#fff; margin:0 }
.top { background:linear-gradient(90deg,#ff0000,#ff6600); padding:16px; border-radius:14px; text-align:center; margin-bottom:12px }
.sync { background:#001a00; border:1px solid #0f0; padding:10px; border-radius:10px; text-align:center; margin:10px 0; color:#0f0 }
.card { background:#1e1e1e; border-radius:12px; padding:16px; margin:12px 0; border-left:6px solid #ff0000; }
.th { color:#ff4444; font-size:1.6em; font-weight:800; }
.en { color:#ffeb3b; font-size:1.0em; }
.map-th { color:#ff8888; } .map-en { color:#ffe082; }
.timer { font-size:1.2em; margin-top:8px; }
button { background:#ff0000; color:white; border:none; padding:8px 14px; border-radius:8px; cursor:pointer; margin-top:8px; }
button:hover { background:#cc0000; }
.filter { margin:10px 0; }
.filter button { background:#333; margin-right:6px; }
.filter button.active { background:#ff0000; }
#clock { font-size:1.1em; color:#0f0; text-align:center; margin:6px }
.status { background:#111; border:1px solid #333; padding:8px; border-radius:8px; margin:8px 0; font-size:13px; color:#aaa }
</style>
</head>
<body>
<div class="top"><h1>🎮 Gem Boss Timer TH - SYNC</h1><div>Discord + Website ซิงค์กัน 100%</div></div>
<div class="sync">🔗 SYNC MODE: เว็บกับดิสคอร์ดใช้เวลาเดียวกัน | กด Kill ที่ไหน อีกที่ก็อัปเดตทันที</div>
<div id="clock"></div>
<div class="status" id="botStatus">⏳ กำลังเช็คสถานะบอท...</div>

<div style="background:#2a0000; border:2px solid #ff0000; border-radius:12px; padding:14px; margin:16px 0;">
  <div style="font-size:1.1em; font-weight:800; color:#fff; margin-bottom:10px;">🔄 RESET บอส (ซิงค์ไปดิสด้วย)</div>
  <button onclick="resetAll()" style="background:#ff0000; font-size:1.1em; padding:12px 20px; font-weight:800;">🔄 RESET ทุกตัว 12 ตัว</button>
  <div style="margin-top:10px;">
    <button onclick="resetCity('reboldoeux')" style="background:#ff6600;">Reset Reboldoeux (4)</button>
    <button onclick="resetCity('coimbra')" style="background:#ffaa00; color:#000">Reset Coimbra (4)</button>
    <button onclick="resetCity('auch')" style="background:#aa00ff;">Reset Auch (4)</button>
  </div>
  <div id="resetMsg" style="color:#0f0; margin-top:8px;"></div>
</div>

<div class="filter">
<button class="active" onclick="filterCity('all', event)">ทั้งหมด 12</button>
<button onclick="filterCity('reboldoeux', event)">รีโบลโดซ์</button>
<button onclick="filterCity('coimbra', event)">คอยมบรา</button>
<button onclick="filterCity('auch', event)">อูช</button>
</div>

<div id="bossList"></div>

<script>
let bosses = [];
let currentFilter='all';
async function load() {
  const res = await fetch('/api/bosses');
  bosses = await res.json();
  render();
  const s = await fetch('/api/status').then(r=>r.json());
  document.getElementById('botStatus').innerHTML = `🤖 บอท: ${s.bot_online?'🟢 ออนไลน์':'🔴 ออฟไลน์'} | ห้อง: ${s.channel_id||'ไม่ได้ตั้ง'} | Sync: ${s.timers_count} ตัว | อัปเดตล่าสุด: ${new Date().toLocaleTimeString('th-TH')}`;
}
function render() {
  const container = document.getElementById('bossList');
  container.innerHTML = '';
  const list = currentFilter==='all'? bosses : bosses.filter(b=>b.city_key===currentFilter);
  list.forEach(b => {
    const next = b.next_spawn ? new Date(b.next_spawn) : null;
    const now = new Date();
    let status='', color='';
    if(!next){ status='⏳ ยังไม่มีเวลา - กด /reset_all'; color='#888' }
    else{
      const diff = next - now;
      if (diff <= 0) { status='🔥 เกิดแล้ว!'; color='#ff0000' }
      else { const m=Math.floor(diff/60000); const h=Math.floor(m/60); const mm=m%60; status=`⏰ อีก ${h}ชม. ${mm}นาที`; color='#0f0' }
    }
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div class="th">## ${b.name_th}</div>
      <div class="en">-# ${b.name_en}</div>
      <div class="map-th">แผนที่: ${b.map_th} | เมือง: ${b.city_th}</div>
      <div class="map-en">Map: ${b.map_en} | City: ${b.city_en}</div>
      <div class="timer" style="color:${color}">${status} - เกิดทุก ${b.respawn_hours}ชม. | Next: ${next? next.toLocaleString('th-TH') : '-'}</div>
      <div style="font-size:12px;color:#888">อัปเดตล่าสุดจาก: ${b.last_source||'-'} | ${b.last_death? new Date(b.last_death).toLocaleString('th-TH') : ''}</div>
      <button onclick="killBoss('${b.id}')">kill boss - แจ้งตาย (ซิงค์ไปดิส)</button>
    `;
    container.appendChild(div);
  });
}
async function killBoss(id) {
  if (!confirm('ยืนยันว่าบอสตาย? จะซิงค์ไป Discord ทันที')) return;
  await fetch('/api/kill', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})});
  document.getElementById('resetMsg').innerText='✅ Kill สำเร็จ - ซิงค์ไปดิสแล้ว';
  load();
}
async function resetAll() {
  if (!confirm('ยืนยัน RESET บอสทั้ง 12 ตัว ใช่ไหม? จะซิงค์ไปดิสด้วย')) return;
  await fetch('/api/reset_all', {method:'POST'});
  document.getElementById('resetMsg').innerText='✅ Reset 12 ตัว - ซิงค์ไปดิสแล้ว - '+new Date().toLocaleString('th-TH');
  load();
}
async function resetCity(city) {
  const name = city==='reboldoeux'?'Reboldoeux': city==='coimbra'?'Coimbra':'Auch';
  if (!confirm('ยืนยัน RESET เมือง '+name+' 4 ตัว ใช่ไหม?')) return;
  await fetch('/api/reset_city', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({city})});
  document.getElementById('resetMsg').innerText='✅ Reset เมือง '+name+' - ซิงค์ไปดิสแล้ว';
  load();
}
function filterCity(key, ev) {
  currentFilter=key;
  document.querySelectorAll('.filter button').forEach(btn=>btn.classList.remove('active'));
  if(ev) ev.target.classList.add('active');
  render();
}
function tick() {
  document.getElementById('clock').innerText='เวลาไทย (ICT): '+new Date().toLocaleString('th-TH',{timeZone:'Asia/Bangkok'});
}
setInterval(tick,1000);
setInterval(load,10000);
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
    bosses = shared.load_bosses()
    timers = shared.load_timers()
    result = []
    for b in bosses:
        t = timers.get(b["id"], {})
        result.append({**b, **t})
    result.sort(key=lambda x: x.get("next_spawn") or "")
    return jsonify(result)

@app.route("/api/status")
def api_status():
    timers = shared.load_timers()
    bot_client, channel_id = shared.get_bot_client()
    return jsonify({
        "bot_online": bot_client is not None and hasattr(bot_client, 'user') and bot_client.user is not None,
        "channel_id": channel_id or os.getenv("CHANNEL_ID"),
        "timers_count": len(timers),
        "sync_mode": "shared.py file lock - Discord + Website same file",
        "time": datetime.now(ICT).isoformat()
    })

def _notify_discord_kill(boss, next_spawn, now, source):
    """ส่งข้อความไป Discord เมื่อมีการ kill จากเว็บ"""
    try:
        bot_client, channel_id = shared.get_bot_client()
        if not bot_client or not channel_id:
            return
        # ใช้ asyncio สร้าง task ส่งข้อความ
        async def send():
            try:
                channel = bot_client.get_channel(int(channel_id))
                if not channel:
                    channel = await bot_client.fetch_channel(int(channel_id))
                import discord
                embed = discord.Embed(
                    title=f"💀 บอสตาย - จาก {source}",
                    description=f"## {boss['name_th']}\n-# {boss['name_en']}\n## {boss['map_th']} | {boss['city_th']}",
                    color=0x555555
                )
                embed.add_field(name="ตายเมื่อ", value=f"<t:{int(now.timestamp())}:F>", inline=True)
                embed.add_field(name="เกิดใหม่", value=f"<t:{int(next_spawn.timestamp())}:F> (<t:{int(next_spawn.timestamp())}:R>)", inline=True)
                embed.add_field(name="ซิงค์จาก", value=f"{source} -> Discord + Website", inline=False)
                await channel.send(content=f"@everyone 💀 {boss['name_th']} ตายจากเว็บ! (ซิงค์)", embed=embed)
                print(f"[WEB->DISCORD] แจ้งตาย {boss['name_th']} ไปดิสแล้ว")
            except Exception as e:
                print(f"[WEB->DISCORD ERROR] {e}")
        # รันใน loop ของบอท
        if bot_client.loop and bot_client.loop.is_running():
            asyncio.run_coroutine_threadsafe(send(), bot_client.loop)
    except Exception as e:
        print(f"[NOTIFY ERROR] {e}")

@app.route("/api/kill", methods=["POST"])
def api_kill():
    data = request.json
    bid = data.get("id")
    result = shared.set_boss_death(bid, None, source="website")
    if not result:
        return jsonify({"error":"not found"}), 404
    _notify_discord_kill(result["boss"], result["next_spawn"], result["now"], "website")
    return jsonify({"ok":True, "next_spawn": result["next_spawn"].isoformat(), "sync":"Discord + Website"})

@app.route("/api/reset_all", methods=["POST"])
def api_reset_all():
    shared.reset_all_bosses(source="website")
    # แจ้งไปดิสด้วย
    try:
        bot_client, channel_id = shared.get_bot_client()
        if bot_client:
            async def send():
                try:
                    channel = bot_client.get_channel(int(channel_id)) or await bot_client.fetch_channel(int(channel_id))
                    await channel.send(content="@everyone 🔄 Reset บอสทั้ง 12 ตัวจากเว็บไซต์! (ซิงค์ Discord + Website)")
                except Exception as e:
                    print(f"[RESET ALL NOTIFY ERROR] {e}")
            if bot_client.loop.is_running():
                import asyncio
                asyncio.run_coroutine_threadsafe(send(), bot_client.loop)
    except:
        pass
    return jsonify({"ok": True, "message": "Reset 12 ตัว - Sync Discord+Website", "sync": True})

@app.route("/api/reset_city", methods=["POST"])
def api_reset_city():
    data = request.json
    city = data.get("city")
    count = shared.reset_city_bosses(city, source="website")
    return jsonify({"ok": True, "city": city, "count": count, "sync": True})

if __name__ == "__main__":
    port = int(os.getenv("WEB_PORT", "5000"))
    print(f"Web SYNC running http://localhost:{port} - ซิงค์กับดิสคอร์ดแล้ว")
    app.run(host="0.0.0.0", port=port, debug=False)
