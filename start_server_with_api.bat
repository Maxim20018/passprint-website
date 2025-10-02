@echo off
echo 🚀 Starting PassPrint Server with API...
echo ========================================
echo.
echo 📋 Checking requirements...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed
    echo 📥 Please install Python from: https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.
echo 📦 Installing dependencies...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Could not install all dependencies automatically
    echo 💡 Try running: pip install -r requirements.txt
)

echo.
echo 🗄️  Initializing database...
python init_db.py >nul 2>&1

echo.
echo 🌐 Starting servers...
echo 📂 Website: http://localhost:5000
echo 🔌 API: http://localhost:5001
echo.
echo 📱 For network access, use your IP address instead of localhost
echo.
python server_api.py

pause