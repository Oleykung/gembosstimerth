
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

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
GUILD_ID = os.getenv("GUILD_ID")  # optional for fast sync
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", "7"))  # ไทย UTC+7
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))

BASE_DIR = Path(__file__).parent
BOSSES_FILE = BASE_DIR / "bosses.json"
TIMERS_FILE = BASE_DIR / "boss_timers.json"

ICT = timezone(timedelta(hours=TIMEZONE_OFFSET))

def load_bosses():
    with open(BOSSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_timers():
    if TIMERS_FILE.exists():
        with open(TIMERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_timers(data):
    with open(TIMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

BOSSES = load_bosses()
BOSSES_BY_ID = {b["id"]: b for b in BOSSES}

# init timers if empty
timers = load_timers()
if not timers:
    now = datetime.now(ICT)
    for b in BOSSES:
        # เริ่มต้นให้เกิดในอีก respawn_hours
        next_spawn = now + timedelta(hours=b.get("respawn_hours", 4))
        timers[b["id"]] = {
            "last_death": None,
            "next_spawn": next_spawn.isoformat(),
            "notified_10min": False,
            "notified_spawn": False
        }
    save_timers(timers)
else:
    timers = load_timers()

def format_boss_big(boss):
    # ตามที่ขอ: ไทยตัวใหญ่ / อังกฤษตัวเล็ก - ชื่อบอส แมพ เมือง แสดงเป็น ## ไทยใหญ่ -# อังกฤษเล็ก
    return (
        f"## {boss['name_th']}\n"
        f"-# {boss['name_en']}\n"
        f"## แผนที่: {boss['map_th']} | เมือง: {boss['city_th']}\n"
        f"-# Map: {boss['map_en']} | City: {boss['city_en']}\n"
        f"**เกิดทุก:** {boss.get('respawn_hours',4)} ชม. | **Respawn:** {boss.get('respawn_hours',4)}h"
    )

def format_boss_ansi(boss, status=""):
    # สำหรับสีแดง ไทย / เหลือง อังกฤษ ในดิส
    # ใช้ ANSI code block
    # 31=แดง, 33=เหลือง, 36=ฟ้า
    return (
        f"```ansi\n"
        f"\u001b[31m{boss['name_th']}\u001b[0m {status}\n"
        f"\u001b[33m{boss['name_en']}\u001b[0m\n"
        f"\u001b[0mแผนที่: {boss['map_th']} | เมือง: {boss['city_th']}\n"
        f"Map: {boss['map_en']} | City: {boss['city_en']}\n"
        f"```"
    )

def get_next_spawn(boss_id):
    t = timers.get(boss_id)
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
    # Sync commands
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
        print(f"Synced to guild {GUILD_ID}")
    else:
        await tree.sync()
        print("Synced global commands")
    if not boss_check_loop.is_running():
        boss_check_loop.start()

# ----- Background Task: แจ้งเตือน 10 นาที + ตอนเกิด @everyone -----
@tasks.loop(seconds=30)
async def boss_check_loop():
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
        next_spawn = datetime.fromisoformat(data["next_spawn"])
        diff = (next_spawn - now).total_seconds()

        # 10 นาทีล่วงหน้า
        if 0 < diff <= 600 and not data.get("notified_10min"):
            embed = discord.Embed(
                title=f"⚠️ บอสใกล้เกิดใน 10 นาที!",
                description=format_boss_big(boss),
                color=0xFFAA00
            )
            embed.add_field(name="เวลาเกิด", value=f"<t:{int(next_spawn.timestamp())}:F> (<t:{int(next_spawn.timestamp())}:R>)", inline=False)
            ansi_text = format_boss_ansi(boss, "- จะเกิดใน 10 นาที")
            await channel.send(content=f"@everyone\n{ansi_text}", embed=embed)
            data["notified_10min"] = True
            updated = True

        # ตอนเกิด
        if -60 < diff <= 0 and not data.get("notified_spawn"):
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
            data["notified_spawn"] = True
            # หลังแจ้งเกิด ให้ตั้งเวลารอบใหม่? จะไม่ตั้งจนกว่าจะ kill
            # แต่ถ้าเป็นบอสแบบ fixed time ให้รีเซ็ตเอง
            updated = True

        # ถ้าเลยเวลาเกิดไปแล้ว 5 นาที ยังไม่มี kill ให้รีเซ็ต notified_spawn เพื่อไม่สแปม
        if diff < -300 and data.get("notified_spawn"):
            # ไม่รีเซ็ตเวลา รอ kill command
            pass

    if updated:
        save_timers(timers)

# ----- Autocomplete -----
async def boss_autocomplete(interaction: discord.Interaction, current: str):
    current = current.lower()
    choices = []
    for b in BOSSES:
        if current in b["name_th"].lower() or current in b["name_en"].lower() or current in b["id"]:
            choices.append(app_commands.Choice(name=f"{b['name_th']} / {b['name_en']}", value=b["id"]))
    return choices[:25]

# ----- Slash Command: /boss -----
@tree.command(name="boss", description="เช็คเวลาบอส Granado Espada M ทั้ง 12 ตัว")
@app_commands.describe(city="กรองตามเมือง: reboldoeux / coimbra / auch")
@app_commands.choices(city=[
    app_commands.Choice(name="เมืองรีโบลโดซ์ / Reboldoeux", value="reboldoeux"),
    app_commands.Choice(name="ท่าเรือคอยมบรา / Port of Coimbra", value="coimbra"),
    app_commands.Choice(name="เมืองอูช / City of Auch", value="auch"),
])
async def boss_command(interaction: discord.Interaction, city: str = None):
    await interaction.response.defer()
    now = datetime.now(ICT)
    filtered = BOSSES
    if city:
        filtered = [b for b in BOSSES if b["city_key"] == city]

    embed = discord.Embed(
        title="📜 ตารางบอส Granado Espada M - เซิร์ฟไทย",
        description="ไทยตัวใหญ่ ## / อังกฤษตัวเล็ก -# | แดง=ไทย เหลือง=อังกฤษ ใน ANSI",
        color=0x00FFAA
    )

    lines = []
    ansi_blocks = []
    for b in filtered:
        bid = b["id"]
        next_spawn = get_next_spawn(bid)
        if next_spawn:
            ts = f"<t:{int(next_spawn.timestamp())}:R> (<t:{int(next_spawn.timestamp())}:t>)"
            remaining = next_spawn - now
            status = f"⏰ {ts}"
        else:
            status = "ไม่พบเวลา"
        
        # Embed field แบบที่ขอ ## ไทยใหญ่ -# อังกฤษเล็ก
        embed.add_field(
            name=f"{b['name_th']} / {b['name_en']}",
            value=f"## {b['name_th']}\n-# {b['name_en']}\n## {b['map_th']} | {b['city_th']}\n-# {b['map_en']} | {b['city_en']}\n{status}\n",
            inline=False
        )
        # สำหรับแสดงในข้อความหลักด้วย
        lines.append(f"## {b['name_th']}\n-# {b['name_en']} - {status}")

    # ส่งเป็น embed + ANSI ตัวอย่าง 3 ตัวแรก
    ansi_example = ""
    for b in filtered[:3]:
        ansi_example += format_boss_ansi(b) + "\n"

    content = "@everyone\n" + "\n".join(lines[:12]) + f"\n\n{ansi_example}\n**สีแดง=ไทย / สีเหลือง=อังกฤษ** ใช้ /kill เพื่อรีเซ็ตเวลาเมื่อบอสตาย"

    # Discord จำกัดความยาว ถ้าเยอะให้ส่งเป็น embed อย่างเดียว
    if len(content) > 1900:
        content = "@everyone ตารางบอสทั้งหมดใน Embed ด้านล่าง"
    
    await interaction.followup.send(content=content, embed=embed)

# ----- Slash Command: /kill -----
@tree.command(name="kill", description="แจ้งว่าบอสตายแล้ว เพื่อรีเซ็ตเวลาเกิดใหม่ (kill boss)")
@app_commands.describe(boss="เลือกบอสที่ตาย")
@app_commands.autocomplete(boss=boss_autocomplete)
async def kill_command(interaction: discord.Interaction, boss: str):
    await interaction.response.defer()
    if boss not in BOSSES_BY_ID:
        await interaction.followup.send(f"❌ ไม่พบบอส id `{boss}`", ephemeral=True)
        return
    
    b = BOSSES_BY_ID[boss]
    now = datetime.now(ICT)
    respawn_h = b.get("respawn_hours", 4)
    next_spawn = now + timedelta(hours=respawn_h)

    timers[boss] = {
        "last_death": now.isoformat(),
        "next_spawn": next_spawn.isoformat(),
        "notified_10min": False,
        "notified_spawn": False
    }
    save_timers(timers)

    embed = discord.Embed(
        title=f"💀 บอสตาย - รีเซ็ตเวลา",
        description=format_boss_big(b),
        color=0x555555
    )
    embed.add_field(name="ตายเมื่อ", value=f"<t:{int(now.timestamp())}:F>", inline=True)
    embed.add_field(name="เกิดใหม่", value=f"<t:{int(next_spawn.timestamp())}:F> (<t:{int(next_spawn.timestamp())}:R>)", inline=True)

    ansi = format_boss_ansi(b, f"- ตายแล้ว จะเกิดใหม่ใน {respawn_h} ชม.")

    await interaction.followup.send(content=f"@everyone\n{ansi}", embed=embed)

# ----- Slash Command: /setboss -----
@tree.command(name="setboss", description="ตั้งเวลาบอสจริงเซิฟไทย (แก้ไฟล์ให้ตรงเซิฟ) - แอดมิน")
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
        # อัพเดตไฟล์ bosses.json ด้วย
        with open(BOSSES_FILE, "w", encoding="utf-8") as f:
            json.dump(BOSSES, f, ensure_ascii=False, indent=2)

    now = datetime.now(ICT)
    if next_spawn_minutes is not None:
        next_spawn = now + timedelta(minutes=next_spawn_minutes)
    else:
        next_spawn = now + timedelta(hours=b.get("respawn_hours", 4))

    timers[boss] = {
        "last_death": now.isoformat() if next_spawn_minutes is None else timers.get(boss, {}).get("last_death"),
        "next_spawn": next_spawn.isoformat(),
        "notified_10min": False,
        "notified_spawn": False
    }
    save_timers(timers)

    await interaction.followup.send(
        f"✅ ตั้งค่า {b['name_th']} / {b['name_en']} เรียบร้อย\n"
        f"Respawn: {b['respawn_hours']}h\n"
        f"Next: <t:{int(next_spawn.timestamp())}:F>",
        ephemeral=True
    )

# ----- Slash Command: /boss_web -----
@tree.command(name="boss_web", description="ลิงก์เว็บดูบอส (ชื่อไทยแดง อังกฤษเหลือง)")
async def boss_web_command(interaction: discord.Interaction):
    port = WEB_PORT
    await interaction.response.send_message(
        f"🌐 เว็บดูบอส: http://localhost:{port}\n"
        f"ชื่อบอสภาษาไทยสีแดง อังกฤษสีเหลือง\n"
        f"รัน `python web.py` เพื่อเปิดเว็บ",
        ephemeral=True
    )


# ----- Slash Command: /reset_all -----
@tree.command(name="reset_all", description="RESET บอสทุกตัว (12 ตัว) - ตั้งเวลาเกิดใหม่ทั้งหมด")
async def reset_all_command(interaction: discord.Interaction):
    await interaction.response.defer()
    now = datetime.now(ICT)
    for b in BOSSES:
        next_spawn = now + timedelta(hours=b.get("respawn_hours", 4))
        timers[b["id"]] = {
            "last_death": now.isoformat(),
            "next_spawn": next_spawn.isoformat(),
            "notified_10min": False,
            "notified_spawn": False
        }
    save_timers(timers)
    embed = discord.Embed(title="🔄 RESET บอสทุกตัวเรียบร้อย!", description="รีเซ็ตบอส 12 ตัว - Reboldoeux 4 / Coimbra 4 / Auch 4", color=0xFF0000)
    for b in BOSSES:
        ns = get_next_spawn(b["id"])
        embed.add_field(name=f"{b['name_th']} / {b['name_en']}", value=f"## {b['name_th']}\n-# {b['name_en']}\nเกิดใหม่ <t:{int(ns.timestamp())}:R>", inline=False)
    await interaction.followup.send(content="@everyone 🔄 Reset บอสทุกตัวแล้ว!", embed=embed)

# ----- Slash Command: /reset_city -----
@tree.command(name="reset_city", description="RESET บอสตามเมือง")
@app_commands.describe(city="เลือกเมืองที่จะ reset")
@app_commands.choices(city=[
    app_commands.Choice(name="เมืองรีโบลโดซ์ / Reboldoeux", value="reboldoeux"),
    app_commands.Choice(name="ท่าเรือคอยมบรา / Port of Coimbra", value="coimbra"),
    app_commands.Choice(name="เมืองอูช / City of Auch", value="auch"),
])
async def reset_city_command(interaction: discord.Interaction, city: str):
    await interaction.response.defer()
    now = datetime.now(ICT)
    count = 0
    for b in BOSSES:
        if b["city_key"] == city:
            next_spawn = now + timedelta(hours=b.get("respawn_hours", 4))
            timers[b["id"]] = {"last_death": now.isoformat(), "next_spawn": next_spawn.isoformat(), "notified_10min": False, "notified_spawn": False}
            count += 1
    save_timers(timers)
    await interaction.followup.send(content=f"@everyone 🔄 Reset บอสเมือง {city} จำนวน {count} ตัวเรียบร้อย!")

if __name__ == "__main__":

    if not DISCORD_TOKEN:
        print("❌ ไม่พบ DISCORD_TOKEN ใน .env")
        exit(1)
    client.run(DISCORD_TOKEN)
