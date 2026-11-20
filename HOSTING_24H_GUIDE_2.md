# รันบอท Discord 24 ชม. - Gem Boss Timer TH

## วิธีที่ 1: Render.com - ฟรี ง่ายสุด (แนะนำ)

1. สมัคร https://render.com ด้วย GitHub
2. New > Web Service > Connect GitHub repo นี้ (หรือ Upload)
3. เลือก:
   - Build Command: pip install -r requirements.txt
   - Start Command: python main.py
   - Region: Singapore (ใกล้ไทยสุด เร็วสุด)
4. ใส่ Env Vars:
   - DISCORD_TOKEN=โทเคนของคุณ
   - CHANNEL_ID=IDห้องแจ้งเตือน
   - GUILD_ID=IDเซิร์ฟ
   - WEB_PORT=10000
5. กด Create -> รอ 2 นาที บอทออนไลน์ 24 ชม.

**ทริคไม่ให้หลับ:** Render ฟรีจะหลับหลัง 15 นาทีถ้าไม่มีคนเข้าเว็บ
- ไป https://uptimerobot.com สมัครฟรี
- Add Monitor > HTTP(s) > ใส่ URL ของ Render ที่ได้มา เช่น https://gem-boss-bot-th.onrender.com
- ตั้ง Every 5 Minutes -> มันจะ ping เว็บคุณทุก 5 นาที บอทจะไม่หลับ 24 ชม.

## วิธีที่ 2: Railway.app - ฟรี $5/เดือน ไม่หลับ

1. ไป https://railway.app สมัครด้วย GitHub
2. New Project > Deploy from GitHub Repo
3. ใส่ Variables เหมือนด้านบน
4. Deploy -> ได้ URL + บอทออนไลน์ 24 ชม. ไม่ต้องใช้ UptimeRobot

## วิธีที่ 3: Fly.io - ฟรีตลอดชีพ

```bash
# ติดตั้ง flyctl
curl -L https://fly.io/install.sh | sh
fly auth signup
fly launch --no-deploy
# แก้ fly.toml ใส่ env
fly secrets set DISCORD_TOKEN=xxx CHANNEL_ID=xxx GUILD_ID=xxx
fly deploy
```
ได้บอทออนไลน์ 24 ชม. ฟรี (มีเครื่องเล็กฟรี 3 เครื่อง)

## วิธีที่ 4: VPS ไทย ถูกสุด

- HostAtom / Ruk-Com / Bangmod VPS ราคา 99-199 บาท/เดือน
- ใช้ Ubuntu 22.04
```bash
sudo apt update && sudo apt install python3 python3-pip git -y
git clone <repo> && cd repo
pip3 install -r requirements.txt
# ใส่ .env
# รันแบบ 24 ชม. ด้วย pm2
sudo npm install -g pm2
pm2 start main.py --interpreter python3 --name gem-boss
pm2 save
pm2 startup
```
บอทจะรัน 24 ชม. แม้ปิดเครื่อง SSH

## วิธีที่ 5: Replit (เก่า แต่ยังใช้ได้)

1. ไป https://replit.com สร้าง Python Repl
2. อัปไฟล์ทั้งหมดไป
3. ใส่ Secrets (DISCORD_TOKEN etc)
4. กด Run
5. ใช้ UptimeRobot ping URL Repl เพื่อไม่ให้หลับ

## เช็คว่าบอทออนไลน์ 24 ชม. ไหม?

- ดูใน Discord บอทต้องขึ้นสีเขียวตลอด
- ดู Log ใน Render/Railway ว่าไม่มี Error
- ทดสอบพิมพ์ /boss ในดิส ต้องตอบตลอด

## ปัญหาที่เจอบ่อย

- บอทออฟไลน์หลังปิดคอม -> ปกติ ต้องเอาไปรันบน Cloud (Render/Railway/Fly)
- Token Invalid -> ไปรีเซ็ต Token ใหม่ใน Discord Developer Portal
- Channel ID ผิด -> เปิด Developer Mode แล้ว Copy ID ใหม่

แนะนำสุด: Render + UptimeRobot ฟรี 100% ทำ 5 นาทีจบ 24 ชม.
