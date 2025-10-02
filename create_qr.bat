@echo off
echo ========================================
echo       QR Code Generator
echo ========================================
echo.
echo Creating QR code for your website...
echo.

cd /d "%~dp0"
python qr_generator.py

echo.
echo ========================================
echo.
echo QR code saved as: qr_code.png
echo Open the PNG file to see the QR code
echo.
pause