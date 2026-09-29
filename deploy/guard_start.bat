@echo off
rem يبدأ حارس إعادة التشغيل التلقائي في الخلفية (بلا نافذة)
cd /d "%~dp0.."
start "" /min "C:\Python314\pythonw.exe" "%~dp0guard.py"
