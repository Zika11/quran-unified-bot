@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo تشغيل البوت في الخلفية (اللوج: logs\bot.out.log)...
start "" /b "C:\Python314\python.exe" -u -m app.main > "logs\bot.out.log" 2>&1
timeout /t 3 >nul
echo تم. للتحقق: type logs\bot.out.log
