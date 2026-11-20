# Granado Espada M - Boss Bot TH [พร้อมรัน Discord สมบูรณ์]

## ✅ สิ่งที่มีในโฟลเดอร์นี้
- bot.py = บอท Discord หลัก (Slash Command /boss /kill /setboss)
- web.py = เว็บดูบอส ไทยแดง เหลืองอังกฤษ
- main.py = รันบอท + เว็บพร้อมกัน (แนะนำ)
- bosses.json = บอส 12 ตัว Reboldoeux, Coimbra, Auch พร้อม map_th/city_th
- boss_timers.json = ไฟล์เก็บเวลาบอส (auto gen)
- .env = ใส่โทเคนบอท
- requirements.txt
- run.bat / run.sh = ดับเบิ้ลคลิกรันได้เลย

## 🚀 วิธีติดตั้งแบบสมบูรณ์ (3 นาที)

### 1. สร้างบอท Discord
1. ไป https://discord.com/developers/applications
2. New Application > Bot > Reset Token > Copy Token
3. เอา Token มาใส่ในไฟล์ .env ตรง DISCORD_TOKEN=
4. ในหน้า Bot เปิด Intents ทั้ง 3 ตัว: Presence, Server Members, Message Content
5. ไปหน้า OAuth2 > URL Generator > เลือก bot + applications.commands > เลือก Administrator > เอาลิงก์ไปเชิญบอทเข้าเซิร์ฟ

### 2. เอา ID ห้อง + เซิร์ฟ
- เปิด Discord > Settings > Advanced > เปิด Developer Mode
- คลิกขวาที่ห้องที่จะให้บอทแจ้งเตือน > Copy ID > ใส่ใน CHANNEL_ID ใน .env
- คลิกขวาที่ชื่อเซิร์ฟเวอร์ > Copy ID > ใส่ใน GUILD_ID (ใส่แล้วคำสั่งจะขึ้นไวใน 1 นาที)

### 3. รัน
Windows: ดับเบิ้ลคลิก run.bat
Mac/Linux: chmod +x run.sh && ./run.sh

หรือรันเอง:
pip install -r requirements.txt
python main.py

บอทจะออนไลน์ + เว็บจะรันที่ http://localhost:5000

## 📜 คำสั่ง Slash ใน Discord

- /boss [city] - ดูตารางบอสทั้งหมด
  - เลือก city: reboldoeux / coimbra / auch เพื่อกรอง
  - แสดงแบบ ## ไทยใหญ่ -# อังกฤษเล็ก ตามที่ขอ

- /kill boss:เลือกบอส - แจ้งว่าบอสตายแล้ว รีเซ็ตเวลาเกิดใหม่ + แท็ก @everyone

- /setboss boss:เลือกบอส respawn_hours:ชั่วโมง next_spawn_minutes:นาที
  - ใช้ตั้งเวลาบอสจริงเซิร์ฟไทย เช่น /setboss boss:ฮิลล์ ไจแอนท์ respawn_hours:4 next_spawn_minutes:240

- /boss_web - เอาลิงก์เว็บ

## 🔔 การแจ้งเตือน
- 10 นาทีล่วงหน้า: @everyone + Embed ส้ม + ANSI ไทยแดง อังกฤษเหลือง
- ตอนเกิด: @everyone + Embed แดง + ANSI เกิดแล้ว NOW!
- ในเว็บ: การ์ดสีแดง ไทยแดง #ff4444 / อังกฤษเหลือง #ffeb3b + ปุ่ม kill boss

## ⚙️ ปรับเวลาบอสจริงเซิร์ฟไทย
แก้ไฟล์ bosses.json:
"respawn_hours": 4

หรือใช้ /setboss ในดิสได้เลย เวลาจะเซฟลง boss_timers.json อัตโนมัติ

ค่าเริ่มต้นที่ตั้งไว้ (ตามแพทช์ SEA):
- Reboldoeux 4 ชม. (3~5 fragment)
- Coimbra 6 ชม. (10~15 fragment)
- Auch 8 ชม. (20~30 fragment)

## ❓ แก้ปัญหา
- บอทไม่ตอบ: เช็คว่าใส่ GUILD_ID แล้วรอ 1 นาที หรือใช้ global sync รอ 1 ชม.
- ไม่แจ้งเตือน: เช็ค CHANNEL_ID และบอทมีสิทธิ์ส่งข้อความ + @everyone ในห้องนั้น
- เว็บไม่ขึ้น: เช็คพอร์ต 5000 ไม่ชนโปรแกรมอื่น แก้ WEB_PORT ใน .env ได้

Made for Oley Jirakarin - Udon Thani
