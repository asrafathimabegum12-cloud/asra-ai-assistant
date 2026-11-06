
@echo off
title Project1 Website Launcher

cd /d "C:\Users\Admin\OneDrive\Desktop\project1"

echo Closing old website servers if they are running...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports = @(5501,8018); foreach ($port in $ports) { Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }"

timeout /t 2 /nobreak >nul

echo Starting backend...
start "Project1 Backend" cmd /k "cd /d C:\Users\Admin\OneDrive\Desktop\project1 && .venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8018"

timeout /t 3 /nobreak >nul

echo Starting frontend...
start "Project1 Frontend" cmd /k "cd /d C:\Users\Admin\OneDrive\Desktop\project1\frontend && ..\.venv\Scripts\python.exe -m http.server 5501"

timeout /t 2 /nobreak >nul

start "" "http://localhost:5501/"

echo Website launcher finished. Keep the server windows open.
