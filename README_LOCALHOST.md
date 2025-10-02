# 🚀 PassPrint Local Server Setup

## ⚠️ Current Situation
Python is not installed on your system. Here are your options:

## Option 1: Direct HTML Opening (IMMEDIATE - No Setup Required)
1. Navigate to your `passprint-website` folder
2. Double-click `open_website.bat`
3. OR simply double-click `index.html`
4. The website opens instantly in your browser

## Option 2: Install Python (Recommended for Server Features)
1. Download Python from: https://python.org
2. Install with "Add Python to PATH" checked
3. Then use Option 1 above with `start_server.bat`

## Option 3: Use Node.js (Alternative)
If you have Node.js installed:
```bash
cd "C:\Users\USER\Documents\passprint-website"
node simple_server.js
```

## 🌐 Access Methods

Once the server is running, you can access PassPrint from:

- **Local machine**: `http://localhost:8000`
- **Other devices on same network**: `http://192.168.1.100:8000` (replace with your actual IP)
- **Mobile devices**: Use your computer's IP address with port 8000

## 📱 For Presentations

### To show on other devices:
1. Make sure all devices are on the same WiFi network
2. Find your computer's IP address:
   - Windows: Open Command Prompt → type `ipconfig` → look for "IPv4 Address"
   - The server will also display your IP when it starts
3. Others can visit: `http://YOUR_IP:8000`

### To show in other applications:
- Copy the URL `http://localhost:8000`
- Paste it in any browser or application that can display web content

## 🛠️ Troubleshooting

### "Python not found" error:
1. Install Python from: https://python.org
2. During installation, check "Add Python to PATH"
3. Restart your computer

### Port 8000 already in use:
- Close other applications using port 8000
- Or modify the PORT variable in server.py

### Can't access from other devices:
1. Make sure all devices are on the same network
2. Check your firewall settings
3. Try disabling VPN if using one

## 📁 File Structure
```
passprint-website/
├── index.html          # Main website
├── server.py          # Python server
├── start_server.bat   # Windows launcher
├── run_localhost.py   # Alternative launcher
├── css/
│   └── style.css
├── js/
│   └── script.js
├── images/            # All images
├── videos/            # All videos
└── pages/             # Other pages
```

## 🔄 To Stop the Server
- Press `Ctrl+C` in the terminal/command prompt
- Close the command window
- Or simply close the terminal

## 💡 Tips
- The server will automatically reload when you refresh the browser
- All forms work with external services (Formspree, Mailchimp, Stripe)
- Images and videos are served locally for fast loading
- No internet required for local viewing (except for external form submissions)

## 🚨 Important Notes
- The server only runs while the command window is open
- For permanent hosting, deploy to Netlify/Vercel as discussed previously
- External services (forms, payments) require internet connection and API setup