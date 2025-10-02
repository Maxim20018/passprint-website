@echo off
echo ========================================
echo    🚀 PassPrint Website Launcher
echo ========================================
echo.
echo 📁 Starting local server...
echo 🌐 Will be available at: http://localhost:8000
echo 📱 For other devices: http://YOUR_IP:8000
echo.
echo Press any key to start...
pause >nul

cd /d "%~dp0"
echo.
echo ========================================
echo             SERVER STARTING...
echo ========================================
python server.py

echo.
echo ========================================
echo          SERVER STOPPED
echo ========================================
echo.
echo Thank you for using PassPrint!
pause