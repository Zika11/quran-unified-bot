@echo off
rem Install auto-restart guard into the user Startup folder (no admin needed).
setlocal
set "PROJ=%~dp0.."
for %%I in ("%PROJ%") do set "PROJ=%%~fI"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TARGET=%STARTUP%\QuranBotGuard.cmd"
> "%TARGET%" echo @echo off
>> "%TARGET%" echo cd /d "%PROJ%"
>> "%TARGET%" echo start "" /min "C:\Python314\pythonw.exe" "%PROJ%\deploy\guard.py"
echo [OK] installed: %TARGET%
echo Target project: %PROJ%
endlocal
