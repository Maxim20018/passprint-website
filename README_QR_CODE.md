# 📱 QR Code Access for PassPrint

## 🎯 What This Does
Creates a QR code that automatically opens your PassPrint website on mobile devices when scanned.

## 🚀 How to Use

### Step 1: Start Your Server
```bash
# Double-click your desktop launcher: PassPrint_Simple.bat
# OR run in terminal:
cd "C:\Users\USER\Documents\passprint-website"
python server.py
```

### Step 2: Create QR Code
```bash
# Run the QR generator:
python qr_generator.py
# OR double-click: create_qr.bat
```

### Step 3: Share with Others
- QR code saved as: `qr_code.png`
- Open the PNG file to see the QR code
- Others scan it with their phone camera
- Automatically opens your website!

## 🌐 How It Works

1. **Server starts** on your computer (IP: 10.95.115.195)
2. **QR code created** with URL: `http://10.95.115.195:5000`
3. **Phone scans QR** → automatically opens your website
4. **No typing needed** - just scan and go!

## 📁 Files Created
```
passprint-website/
├── 📱 qr_generator.py      # Python QR generator
├── 🚀 create_qr.bat        # Windows launcher
├── 📷 qr_code.png          # Generated QR code (after running)
└── [your website files]
```

## ✅ Benefits
- ✅ **No manual typing** of IP addresses
- ✅ **Instant access** for mobile devices
- ✅ **Professional presentation** tool
- ✅ **Easy sharing** with clients/customers
- ✅ **Works offline** once server is running

## 🔧 Requirements
- Python installed (already working)
- QR code library: `pip install qrcode[pil]`

## 📱 Perfect For:
- Client presentations
- Demo sessions
- Portfolio showcase
- Trade shows
- Business meetings

**Your PassPrint website is now mobile-accessible with QR codes!** 🎉