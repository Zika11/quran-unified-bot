@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "logs\bot.pid" (
  set /p PID=<"logs\bot.pid"
  echo إيقاف البوت (PID=%PID%)...
  taskkill /PID %PID% /F >nul 2>&1
  del /q "logs\bot.pid" >nul 2>&1
  echo تم الإيقاف.
) else (
  echo لا يوجد ملف PID. البحث عن عمليات app.main...
  for /f "tokens=2" %%p in ('wmic process where "commandline like '%%app.main%%' and name='python.exe'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    taskkill /PID %%p /F >nul 2>&1
    echo أوقفت PID %%p
  )
)
pause >nul
