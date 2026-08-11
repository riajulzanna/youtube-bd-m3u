@echo off
cd /d "%~dp0"
py -m yt_dlp --version
if errorlevel 1 (
 echo yt-dlp is not available. Run: py -m pip install -U yt-dlp
 pause
 exit /b 1
)
py generate.py
echo.
echo Output: %CD%\youtube_bd.m3u
pause
