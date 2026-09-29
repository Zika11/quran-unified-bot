@echo off
chcp 65001 >nul
title Quran Unified Bot
cd /d "%~dp0"
echo ============================================
echo   بوت القرآن الموحّد - تشغيل
echo ============================================
if not exist ".env" (
  echo [خطأ] لا يوجد ملف .env — انسخ .env.example إلى .env واملأ BOT_TOKEN
  pause
  exit /b 1
)
"C:\Python314\python.exe" -u -m app.main
echo.
echo [توقف البوت] اضغط أي زر للإغلاق.
pause >nul
