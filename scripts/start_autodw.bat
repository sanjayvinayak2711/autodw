@echo off
echo Starting AutoDW with auto-browser opening...
echo.

REM Stop any existing container
docker stop autodw-container 2>nul
docker rm autodw-container 2>nul

REM Run container
echo Starting Docker container...
docker run -d -p 8000:8000 --name autodw-container autodw

REM Wait for server to start
echo Waiting for server to be ready...
timeout /t 3 /nobreak >nul

REM Open browser with correct URL
echo Opening AutoDW at http://localhost:8000
start http://localhost:8000

echo.
echo AutoDW is running at: http://localhost:8000
echo To stop: docker stop autodw-container
pause
