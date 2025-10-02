@echo off
echo ========================================
echo     🚀 PassPrint Quick Launch
echo ========================================
echo.
echo 📊 Getting your IP address...
echo.

REM Get IPv4 address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
    set "IP=%%a"
    REM Remove leading space
    set "IP=!IP:~1!"
    echo 🌐 Your IP address: !IP!
)

echo.
echo ========================================
echo.
echo 📱 Access URLs:
echo   Local:      http://localhost:8000
echo   Network:    http://!IP!:8000
echo.
echo ========================================
echo.
echo Press any key to start the server...
pause >nul

echo.
echo ========================================
echo         Starting Server...
echo ========================================

cd /d "%~dp0"
python server.py

echo.
echo Server stopped.
pause