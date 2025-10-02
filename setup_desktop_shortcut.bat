@echo off
echo ========================================
echo    📁 Setting up Desktop Shortcut
echo ========================================
echo.

REM Get the current directory
set "SOURCE_DIR=%~dp0"
set "LAUNCHER=%SOURCE_DIR%Desktop_Launcher.bat"

REM Create the launcher if it doesn't exist
if not exist "%LAUNCHER%" (
    echo Creating launcher file...
    copy "%SOURCE_DIR%Desktop_Launcher.bat" "%LAUNCHER%" >nul 2>&1
)

REM Copy to desktop
echo 📂 Copying to desktop...
copy "%LAUNCHER%" "%USERPROFILE%\Desktop\PassPrint_Website.lnk" >nul 2>&1

if exist "%USERPROFILE%\Desktop\PassPrint_Website.lnk" (
    echo ✅ SUCCESS: Desktop shortcut created!
    echo 🖥️  Look for "PassPrint_Website.lnk" on your desktop
    echo.
    echo ========================================
    echo              INSTRUCTIONS
    echo ========================================
    echo 1. Double-click the desktop shortcut
    echo 2. Server will start automatically
    echo 3. Access at: http://localhost:8000
    echo 4. For other devices: Find your IP below
    echo.
    echo ========================================
    echo.
    echo 🔍 Your Network Information:
    ipconfig | findstr /C:"IPv4 Address"
    echo.
    echo ========================================
    echo.
    echo 💡 Tip: Keep the command window open to keep server running
    echo    Close it or press Ctrl+C to stop the server
    echo.
) else (
    echo ❌ Failed to create desktop shortcut
    echo    Please manually copy Desktop_Launcher.bat to your desktop
)

echo.
pause