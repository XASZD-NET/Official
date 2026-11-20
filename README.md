# ABSOLUTE DARKGPT 6767 — Web + Backend

รวมหน้าเว็บ HTML/CSS/JavaScript, Flask API, Scapy Beacon receiver และ SQLite ไว้ในโปรเจกต์เดียว

## ขอบเขตความเป็นส่วนตัว
- สแกนเฉพาะ 802.11 Beacon frames เพื่อทำรายการ Access Point
- ไม่เก็บ Probe Request, MAC ของ Client หรือข้อมูลเพื่อระบุตัว/ติดตามอุปกรณ์ของบุคคลอื่น
- ไม่เชื่อมต่อ ไม่ส่งแพ็กเก็ต ไม่รบกวนการสื่อสาร และไม่ข้ามการควบคุมการเข้าถึง
- ใช้เฉพาะอุปกรณ์/พื้นที่ที่คุณเป็นเจ้าของหรือได้รับอนุญาต
- เว็บเซิร์ฟเวอร์ bind ที่ `127.0.0.1` เป็นค่าเริ่มต้น ไม่เปิดให้เครื่องอื่นใน LAN เข้าถึงโดยไม่ตั้งใจ

## โครงสร้าง
```text
ABSOLUTE_DARKGPT_6767_WEB/
├── web/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── server/
│   ├── app.py
│   ├── scanner.py
│   ├── processor.py
│   └── storage.py
├── database/
│   └── wifi_data.db       # สร้างเมื่อรันครั้งแรก
├── requirements.txt
├── .env.example
└── README.md
```

## ติดตั้ง
Python 3.10+:
```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

ต้องมี Wi-Fi adapter/driver ที่รองรับ Monitor Mode และตั้งค่า interface ด้วยเครื่องมือของระบบปฏิบัติการก่อนรันแอป ทั้งนี้ความสามารถขึ้นกับฮาร์ดแวร์และไดรเวอร์ โปรเจกต์นี้ไม่เปลี่ยนโหมด adapter ให้อัตโนมัติ

## เริ่มระบบ
Linux/macOS:
```bash
export WIFI_MONITOR_INTERFACE=wlan0mon
python server/app.py
```
Windows PowerShell:
```powershell
$env:WIFI_MONITOR_INTERFACE="ชื่ออินเทอร์เฟซที่รองรับ"
python server/app.py
```
เปิด `http://127.0.0.1:5000`

หากต้องการใช้โหมดหน้าเว็บอย่างเดียวโดยยังไม่มี adapter ให้เปิดหน้าเว็บและตรวจสอบ API ได้ แต่ปุ่มเริ่มสแกนจะแจ้งว่าต้องกำหนด interface ก่อน

## API
- `GET /api/health` — ตรวจสอบบริการ
- `GET /api/status` — สถานะและรัศมี
- `GET /api/devices?radius=100` — รายการ AP
- `POST /api/config` — `{"radius":100}`
- `POST /api/start` — เริ่มสแกนเมื่อกำหนด interface แล้ว
- `POST /api/stop` — หยุดสแกน

## ระยะทางและข้อจำกัด
RSSI ไม่ใช่เครื่องวัดระยะทาง สูตร log-distance ในระบบเป็นเพียงค่าประมาณ ต้องสอบเทียบกับอุปกรณ์และพื้นที่จริง และอาจคลาดเคลื่อนมากจากผนัง การสะท้อนคลื่น เสาอากาศ การวางอุปกรณ์ และกำลังส่ง ระบบจึงไม่สามารถยืนยันว่า Access Point อยู่ในรัศมี 50/100/150 เมตรจริงได้

อะแดปเตอร์หนึ่งตัวมักรับฟังได้ทีละช่องสัญญาณ จึงไม่สามารถรับทุกช่อง 2.4 GHz และ 5 GHz พร้อมกันได้อย่างน่าเชื่อถือ
