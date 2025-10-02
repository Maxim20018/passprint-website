@echo off
echo 🔗 Creating desktop shortcut for PassPrint...
echo 📁 Target: %~dp0index.html
echo 📝 Creating shortcut...

REM Create a temporary VBS script to create the shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\PassPrint.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%~dp0index.html" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%~dp0" >> CreateShortcut.vbs
echo oLink.Description = "PassPrint Website" >> CreateShortcut.vbs
echo oLink.IconLocation = "%~dp0index.html, 0" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript CreateShortcut.vbs
del CreateShortcut.vbs

echo ✅ Desktop shortcut created!
echo 🖥️  Look for "PassPrint.lnk" on your desktop
pause