import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

import shared  # ตัวกลางซิงค์เว็บ+ดิส

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
GUILD_ID = os.getenv("GUILD_ID")
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", "7"))
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))

BASE_DIR = Path(__file__).parent
BOSSES_FILE = BASE_DIR / "bosses.json"
TIMERS_FILE = BASE_DIR / "boss_timers.json"

ICT = timezone(timedelta(hours=TIMEZONE_OFFSET))

def load_bosses():
    return shared.load_bosses()

def load_timers():
    return shared.load_timers()

def save_timers(data):
    return shared.save_timers(data)

BOSSES = load_bosses()
BOSSES_BY_ID = {b["id"]: b for b in BOSSES}

# init timers if empty
timers = load_timers()
if not timers:
    now = datetime.now(ICT)
    for b in BOSSES:
        next_spawn = now + timedelta(hours=b.get("respawn_hours", 4))
        timers[b["id"]] = {
            "last_death": None,
            "next_spawn": next_spawn.isoformat(),
            "notified_10min": False,
            "notified_spawn": False,
            "last_source": "init"
        }
    save_timers(timers)
else:
    timers = load_timers()

def format_boss_big(boss):
    return (
        f"## {boss['name_th']}\n"
        f"-# {boss['name_en']}\n"
        f"## แผนที่: {boss['map_th']} | เมือง: {boss['city_th']}\n"
        f"-# Map: {boss['map_en']} | City: {boss['city_en']}\n"
        f"**เกิดทุก:** {boss.get('respawn_hours',4)} ชม. | **Respawn:** {boss.get('respawn_hours',4)}h"
    )

def format_boss_ansi(boss, status=""):
    return (
        f"```ansi\n"
        f"\u001b[31m{boss['name_th']}\u001b[0m {status}\n"
        f"\u001b[33m{boss['name_en']}\u001b[0m\n"
        f"\u001b[0mแผนที่: {boss['map_th']} | เมือง: {boss['city_th']}\n"
        f"Map: {boss['map_en']} | City: {boss['city_en']}\n"
        f"```"
    )

def get_next_spawn(boss_id):
    t = load_timers().get(boss_id)
    if not t:
        return None
    return datetime.fromisoformat(t["next_spawn"])

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    # เชื่อมกับ shared เพื่อให้เว็บส่งข้อความไปดิสได้
    shared.set_bot_client(client, CHANNEL_ID)
    if GUILD_ID:
        try:
            guild = discord.Object(id=int(GUILD_ID))
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
            print(f"✅ Synced to guild {GUILD_ID} - คำสั่ง /boss /boss_check จะขึ้นทันที")
        except Exception as e:
            print(f"❌ Sync guild {GUILD_ID} ล้มเหลว: {e}")
            await tree.sync()
            print("Synced global instead")
    else:
        await tree.sync()
        print("✅ Synced global commands - รอ 5-60 นาที คำสั่งจะขึ้น")
    if not boss_check_loop.is_running():
        boss_check_loop.start()

# ----- Background Task: แจ้งเตือน 10 นาที + ตอนเกิด @everyone (SYNC v4) -----
@tasks.loop(seconds=10)
async def boss_check_loop():
    global timers
    try:
        timers = load_timers()
    except Exception as e:
        print(f"[LOOP] load timers error: {e}")
        return

    if CHANNEL_ID == 0:
        return
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        try:
            channel = await client.fetch_channel(CHANNEL_ID)
        except:
            return
    now = datetime.now(ICT)
    updated = False
    for boss in BOSSES:
        bid = boss["id"]
        data = timers.get(bid)
        if not data:
            continue
        try:
            next_spawn = datetime.fromisoformat(data["next_spawn"])
        except:
            continue
        diff = (next_spawn - now).total_seconds()

        if 0 < diff <= 600 and not data.get("notified_10min"):
            try:
                embed = discord.Embed(
                    title=f"⚠️ บอสใกล้เกิดใน 10 นาที!",
                    description=format_boss_big(boss),
                    color=0xFFAA00
                )
                embed.add_field(name="เวลาเกิด", value=f"<t:{int(next_spawn.timestamp())}:F> (<t:{int(next_spawn.timestamp())}:R>)", inline=False)
                ansi_text = format_boss_ansi(boss, "- จะเกิดใน 10 นาที")
                await channel.send(content=f"@everyone\n{ansi_text}", embed=embed)
                print(f"[NOTIFY] 10min {boss['name_th']}")
                data["notified_10min"] = True
                updated = True
            except Exception as e:
                print(f"[NOTIFY ERROR] 10min: {e}")

        if -1800 < diff <= 0 and not data.get("notified_spawn"):
            try:
                embed = discord.Embed(
                    title=f"🔥 บอสเกิดแล้ว!",
                    description=format_boss_big(boss),
                    color=0xFF0000
                )
                embed.add_field(name="แผนที่", value=f"{boss['map_th']} ({boss['map_en']})", inline=True)
                embed.add_field(name="เมือง", value=f"{boss['city_th']} ({boss['city_en']})", inline=True)
                embed.add_field(name="เวลา", value=f"<t:{int(now.timestamp())}:F>", inline=False)
                ansi_text = format_boss_ansi(boss, "- เกิดแล้ว NOW!")
                await channel.send(content=f"@everyone บอสเกิดแล้ว!\n{ansi_text}", embed=embed)
                print(f"[NOTIFY] SPAWN {boss['name_th']}")
                data["notified_spawn"] = True
                updated = True
            except Exception as e:
                print(f"[NOTIFY ERROR] SPAWN: {e}")

    if updated:
        save_timers(timers)

@boss_check_loop.before_loop
async def before_boss_loop():
    await client.wait_until_ready()
    print("[LOOP] boss_check_loop ready - เช็คทุก 10 วิ - SYNC กับเว็บแล้ว")

async def boss_autocomplete(interaction: discord.Interaction, current: str):
    current = current.lower()
    choices = []
    for b in BOSSES:
        if current in b["name_th"].lower() or current in b["name_en"].lower() or current in b["id"]:
            choices.append(app_commands.Choice(name=f"{b['name_th']} / {b['name_en']}", value=b["id"]))
    return choices[:25]

# ----- Slash Command: /boss (SYNC) -----
@tree.command(name="boss", description="เช็คเวลาบอส Granado Espada M ทั้ง 12 ตัว")
@app_commands.describe(city="กรองตามเมือง: reboldoeux / coimbra / auch")
@app_commands.choices(city=[
    app_commands.Choice(name="เมืองรีโบลโดซ์ / Reboldoeux", value="reboldoeux"),
    app_commands.Choice(name="ท่าเรือคอยมบรา / Port of Coimbra", value="coimbra"),
    app_commands.Choice(name="เมืองอูช / City of Auch", value="auch"),
])
async def boss_command(interaction: discord.Interaction, city: str = None):
    try:
        await interaction.response.defer(ephemeral=False)
    except:
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            pass
    try:
        now = datetime.now(ICT)
        filtered = BOSSES
        if city:
            filtered = [b for b in BOSSES if b["city_key"] == city]
        current_timers = load_timers()
        embed = discord.Embed(
            title="📜 ตารางบอส Granado Espada M - SYNC Discord+Website",
            description=f"ทั้งหมด {len(filtered)} ตัว | ซิงค์กับเว็บแล้ว | เวลาไทย ICT",
            color=0x00FFAA
        )
        lines = []
        for b in filtered[:12]:
            bid = b["id"]
            t = current_timers.get(bid, {})
            ns_str = t.get("next_spawn")
            if ns_str:
                try:
                    next_spawn = datetime.fromisoformat(ns_str)
                    ts = f"<t:{int(next_spawn.timestamp())}:R>"
                    status = f"⏰ {ts} (<t:{int(next_spawn.timestamp())}:t>)"
                except:
                    status = "เวลาพัง"
            else:
                status = "ยังไม่มีเวลา / พิมพ์ /reset_all"
            field_value = f"## {b['name_th']}\n-# {b['name_en']}\n{status}\n"
            if len(field_value) > 900:
                field_value = field_value[:900]
            embed.add_field(name=f"{b['name_th']}", value=field_value, inline=False)
            lines.append(f"## {b['name_th']} - {status}")
        content_text = "\n".join(lines[:6])
        if len(filtered) > 6:
            content_text += f"\n...และอีก {len(filtered)-6} ตัว ดูใน Embed"
        if len(content_text) > 1800:
            content_text = content_text[:1800]
        await interaction.followup.send(content=content_text, embed=embed)
    except Exception as e:
        print(f"[BOSS CMD ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
        except:
            pass

@tree.command(name="boss_check", description="เช็คเวลาบอส (ชื่อเก่า) - ใช้เหมือน /boss")
@app_commands.describe(city="กรองตามเมือง: reboldoeux / coimbra / auch")
@app_commands.choices(city=[
    app_commands.Choice(name="เมืองรีโบลโดซ์ / Reboldoeux", value="reboldoeux"),
    app_commands.Choice(name="ท่าเรือคอยมบรา / Port of Coimbra", value="coimbra"),
    app_commands.Choice(name="เมืองอูช / City of Auch", value="auch"),
])
async def boss_check_command(interaction: discord.Interaction, city: str = None):
    await boss_command(interaction, city)


# ----- Slash Command: /kill (SYNC) -----
@tree.command(name="kill", description="แจ้งว่าบอสตายแล้ว เพื่อรีเซ็ตเวลาเกิดใหม่ (kill boss) - Sync ไปเว็บด้วย")
@app_commands.describe(boss="เลือกบอสที่ตาย")
@app_commands.autocomplete(boss=boss_autocomplete)
async def kill_command(interaction: discord.Interaction, boss: str):
    try:
        await interaction.response.defer()
    except:
        pass
    if boss not in BOSSES_BY_ID:
        await interaction.followup.send(f"❌ ไม่พบบอส id `{boss}`", ephemeral=True)
        return
    
    result = shared.set_boss_death(boss, None, source="discord")
    if not result:
        await interaction.followup.send("❌ ไม่พบบอส", ephemeral=True)
        return
    b = result["boss"]
    now = result["now"]
    next_spawn = result["next_spawn"]

    embed = discord.Embed(
        title=f"💀 บอสตาย - รีเซ็ตเวลา (Sync ไปเว็บ)",
        description=format_boss_big(b),
        color=0x555555
    )
    embed.add_field(name="ตายเมื่อ", value=f"<t:{int(now.timestamp())}:F>", inline=True)
    embed.add_field(name="เกิดใหม่", value=f"<t:{int(next_spawn.timestamp())}:F> (<t:{int(next_spawn.timestamp())}:R>)", inline=True)
    embed.add_field(name="ซิงค์", value="Discord + Website อัปเดตพร้อมกัน", inline=False)

    ansi = format_boss_ansi(b, f"- ตายแล้ว จะเกิดใหม่ใน {b.get('respawn_hours',4)} ชม.")

    await interaction.followup.send(content=f"@everyone\n{ansi}", embed=embed)

# ----- Slash Command: /setboss (SYNC) -----
@tree.command(name="setboss", description="ตั้งเวลาบอสจริงเซิฟไทย (แก้ไฟล์ให้ตรงเซิฟ) - Sync ไปเว็บด้วย")
@app_commands.describe(
    boss="บอสที่ต้องการตั้ง",
    respawn_hours="ตั้งเวลารีสปอนใหม่เป็นชั่วโมง (เช่น 4)",
    next_spawn_minutes="ตั้งว่าเกิดในอีกกี่นาที (เช่น 60 = เกิดใน 1 ชม.)"
)
@app_commands.autocomplete(boss=boss_autocomplete)
async def setboss_command(interaction: discord.Interaction, boss: str, respawn_hours: int = None, next_spawn_minutes: int = None):
    await interaction.response.defer(ephemeral=True)
    if boss not in BOSSES_BY_ID:
        await interaction.followup.send("ไม่พบบอส", ephemeral=True)
        return
    
    b = BOSSES_BY_ID[boss]
    if respawn_hours:
        b["respawn_hours"] = respawn_hours
        with open(BOSSES_FILE, "w", encoding="utf-8") as f:
            json.dump(BOSSES, f, ensure_ascii=False, indent=2)

    now = datetime.now(ICT)
    if next_spawn_minutes is not None:
        next_spawn = now + timedelta(minutes=next_spawn_minutes)
    else:
        next_spawn = now + timedelta(hours=b.get("respawn_hours", 4))

    timers_data = load_timers()
    timers_data[boss] = {
        "last_death": now.isoformat() if next_spawn_minutes is None else timers_data.get(boss, {}).get("last_death"),
        "next_spawn": next_spawn.isoformat(),
        "notified_10min": False,
        "notified_spawn": False,
        "last_source": "discord setboss"
    }
    save_timers(timers_data)

    await interaction.followup.send(
        f"✅ ตั้งค่า {b['name_th']} / {b['name_en']} เรียบร้อย (Sync ไปเว็บแล้ว)\n"
        f"Respawn: {b['respawn_hours']}h\n"
        f"Next: <t:{int(next_spawn.timestamp())}:F>",
        ephemeral=True
    )

@tree.command(name="boss_web", description="ลิงก์เว็บดูบอส (Sync กับดิสแล้ว)")
async def boss_web_command(interaction: discord.Interaction):
    port = WEB_PORT
    await interaction.response.send_message(
        f"🌐 เว็บดูบอส (Sync กับดิสแล้ว): http://localhost:{port}\n"
        f"กด Kill ในเว็บ = บอทในดิสก็อัปเดตทันที\n"
        f"กด /kill ในดิส = เว็บก็อัปเดตทันที\n",
        ephemeral=True
    )

@tree.command(name="reset_all", description="RESET บอสทุกตัว (12 ตัว) - Sync ไปเว็บด้วย")
async def reset_all_command(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
    except:
        pass
    shared.reset_all_bosses(source="discord reset_all")
    embed = discord.Embed(title="🔄 RESET บอสทุกตัวเรียบร้อย! (Sync ไปเว็บแล้ว)", description="รีเซ็ตบอส 12 ตัว - Reboldoeux 4 / Coimbra 4 / Auch 4 - เว็บก็รีเซ็ตด้วย", color=0xFF0000)
    now = datetime.now(ICT)
    timers_data = load_timers()
    for b in BOSSES[:6]:
        ns_str = timers_data.get(b["id"], {}).get("next_spawn")
        if ns_str:
            try:
                ns = datetime.fromisoformat(ns_str)
                embed.add_field(name=f"{b['name_th']}", value=f"เกิดใหม่ <t:{int(ns.timestamp())}:R>", inline=True)
            except:
                pass
    await interaction.followup.send(content="@everyone 🔄 Reset บอสทุกตัวแล้ว! (เว็บก็รีเซ็ตด้วย)", embed=embed)

@tree.command(name="reset_city", description="RESET บอสตามเมือง - Sync ไปเว็บด้วย")
@app_commands.describe(city="เลือกเมืองที่จะ reset")
@app_commands.choices(city=[
    app_commands.Choice(name="เมืองรีโบลโดซ์ / Reboldoeux", value="reboldoeux"),
    app_commands.Choice(name="ท่าเรือคอยมบรา / Port of Coimbra", value="coimbra"),
    app_commands.Choice(name="เมืองอูช / City of Auch", value="auch"),
])
async def reset_city_command(interaction: discord.Interaction, city: str):
    try:
        await interaction.response.defer()
    except:
        pass
    count = shared.reset_city_bosses(city, source="discord reset_city")
    await interaction.followup.send(content=f"@everyone 🔄 Reset บอสเมือง {city} จำนวน {count} ตัวเรียบร้อย! (เว็บก็รีเซ็ตด้วย)")

@tree.command(name="test_notify", description="ทดสอบว่าบอทส่งแจ้งเตือนได้ไหม")
async def test_notify_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        channel = client.get_channel(CHANNEL_ID) or await client.fetch_channel(CHANNEL_ID)
        await channel.send(content=f"@everyone 🧪 ทดสอบแจ้งเตือน SYNC - บอท+เว็บซิงค์กันแล้ว!\n## ทดสอบ\n-# Test Notify")
        await interaction.followup.send(f"✅ ส่งทดสอบไปห้อง <#{CHANNEL_ID}> แล้ว", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ ส่งไม่ได้: {e}", ephemeral=True)

@tree.command(name="debug", description="เช็คว่าทำไมบอทไม่แจ้งเตือน - ดูเวลา SYNC")
async def debug_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    now = datetime.now(ICT)
    timers_data = load_timers()
    lines = [f"**CHANNEL_ID:** {CHANNEL_ID} (<#{CHANNEL_ID}>)", f"**เวลาไทย:** {now.strftime('%d/%m %H:%M:%S')}", f"**SYNC MODE:** shared.py - Discord+Website same file", f"**บอท:** {client.user}", ""]
    for b in BOSSES:
        data = timers_data.get(b["id"], {})
        ns = data.get("next_spawn", "ไม่มี")
        try:
            dt = datetime.fromisoformat(ns)
            diff = int((dt - now).total_seconds())
            diff_str = f"อีก {diff//60} นาที" if diff>0 else f"เลยมา {-diff//60} นาที"
            flag = f"10min={data.get('notified_10min')} spawn={data.get('notified_spawn')} src={data.get('last_source','-')}"
            lines.append(f"{b['name_th']} - {dt.strftime('%H:%M')} ({diff_str}) {flag}")
        except:
            lines.append(f"{b['name_th']} - เวลาพัง {ns}")
    await interaction.followup.send("\n".join(lines), ephemeral=True)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ ไม่พบ DISCORD_TOKEN ใน .env")
        exit(1)
    client.run(DISCORD_TOKEN)
