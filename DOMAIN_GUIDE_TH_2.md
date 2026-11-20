# จดโดเมน Gem Boss Timer TH - คู่มือฉบับสมบูรณ์

## ชื่อโดเมนที่แนะนำ (เรียงตามความน่าใช้)
1. gembosstimerth.com - ตรงตัวสุด จำง่าย ค้นหาเจอ
2. gemboss-th.com - สั้นกว่า
3. gem-boss-timer.com - อ่านง่าย
4. gembosstimer.com - ถ้ายังว่าง รีบจด
5. gembossth.com - สั้นสุด

เช็คสถานะล่าสุดที่:
- https://www.namecheap.com/domains/registration/results/?domain=gembosstimerth.com
- https://www.cloudflare.com/products/registrar/
- https://th.godaddy.com/domainsearch/find?domainToCheck=gembosstimerth.com

## ราคาโดยประมาณ (Nov 2026)
- Cloudflare Registrar: ~380 บาท/ปี เท่ากันทุกปี ถูกสุดระยะยาว + ฟรี WHOIS Privacy
- Namecheap: ปีแรก ~200 บาท (โปร) ต่ออายุ ~550 บาท/ปี
- GoDaddy TH: ปีแรก 1 บาท (ต้องซื้อ 3 ปี) ต่ออายุ 699 บาท/ปี
- Porkbun: ~390 บาท/ปี เท่ากันทุกปี

แนะนำ: Cloudflare ถ้าเน้นถูกระยะยาว / Namecheap ถ้าอยากเริ่มง่าย

## วิธีจด (5 นาที)
1. สมัครบัญชีที่ผู้ให้บริการ (ใช้อีเมลของคุณ)
2. ค้นหา gembosstimerth.com -> กด Add to Cart
3. เปิด WHOIS Privacy = ฟรี (กันสแปม)
4. จ่ายด้วยบัตรเดบิต/เครดิต TrueMoney Wallet ได้ (Namecheap/GoDaddy รับ)
5. อย่าซื้อ Add-on เพิ่ม (SSL, Email แพง ไม่ต้อง)

## หลังจดแล้ว ชี้โดเมนมาที่เว็บ
### ถ้าใช้ Vercel / Netlify (แนะนำ ฟรี)
- เอาไฟล์ในโฟลเดอร์นี้ไป Deploy ที่ Vercel
- ใน Vercel > Settings > Domains > ใส่ gembosstimerth.com
- ระบบจะให้ค่า DNS มา 2 ตัว:
  - Type A: @ -> 76.76.21.21 (ตัวอย่าง Vercel)
  - Type CNAME: www -> cname.vercel-dns.com
- เอาค่านี้ไปใส่ในหน้า DNS ของที่จดโดเมน รอ 5-30 นาทีก็เข้าได้

### ถ้าใช้ Cloudflare Pages + Cloudflare Registrar (ง่ายสุด)
- จดที่ Cloudflare เลย -> Deploy ที่ Cloudflare Pages
- ระบบจะชี้โดเมนให้อัตโนมัติ ไม่ต้องตั้ง DNS เอง

## DNS ที่ต้องใส่ (ตัวอย่าง)
| Type | Name | Value |
| A | @ | IP จากโฮสติ้ง |
| CNAME | www | โดเมนของโฮสติ้ง |
| TXT | @ | สำหรับยืนยันเจ้าของ (ถ้ามี) |

## เช็คว่าโดเมนใช้ได้ไหม
เข้า https://gembosstimerth.com แล้วต้องเจอหน้า Boss Timer
ถ้ายังไม่ขึ้น รอ DNS 1-24 ชม. แล้วลอง Clear Cache

## โดเมน .th / .co.th
- ราคา ~800-1,200 บาท/ปี ต้องใช้เอกสารบริษัท/บัตรประชาชน + รอ 1-3 วัน
- ไม่แนะนำตอนนี้ ใช้ .com ไปก่อน เร็วกว่าและถูกกว่า
