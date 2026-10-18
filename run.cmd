@echo off
rem ============================================================================
rem  Ardhang Matrimony - local dev launcher (Windows)
rem
rem    run.cmd                  start API + admin + web + mobile
rem    run.cmd --no-mobile      start everything except the Expo dev server
rem    run.cmd api|admin|web|mobile    start a single app
rem
rem  The API runs on SQLite (backend\dev.db) with the mock payment provider, so
rem  no Docker, Postgres or Redis is required for local testing. Redis-backed
rem  features (rate limiting, OTP storage, caches, jobs) fail open when absent.
rem ============================================================================
setlocal EnableExtensions
set "ROOT=%~dp0"
rem Capture the full script path now: `shift` later would corrupt %~f0.
set "SELF=%~f0"

rem ---- Each window re-invokes this file with a role argument. ----
if /I "%~1"=="api"    goto run_api
if /I "%~1"=="admin"  goto run_admin
if /I "%~1"=="web"    goto run_web
if /I "%~1"=="mobile" goto run_mobile

rem ---- Launcher: parse options ----
set "SKIP_MOBILE="
:parse_args
if "%~1"=="" goto launch_all
if /I "%~1"=="--no-mobile" (set "SKIP_MOBILE=1" & shift & goto parse_args)
if /I "%~1"=="nomobile"    (set "SKIP_MOBILE=1" & shift & goto parse_args)
echo Unknown option: %~1
echo Usage: run.cmd [--no-mobile]  ^|  run.cmd api^|admin^|web^|mobile
exit /b 1

:launch_all
title Ardhang local dev launcher
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found on PATH. Install Python 3.11+ from https://www.python.org/downloads/
  pause
  exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found on PATH. Install Node 20+ from https://nodejs.org/
  pause
  exit /b 1
)

echo Opening one window per app:
echo   API     http://localhost:8000   FastAPI, SQLite dev.db, mock payments - no Docker needed
echo   Admin   http://localhost:3001   staff dashboard
echo   Web     http://localhost:3000   end-user web client
if not defined SKIP_MOBILE echo   Mobile  Expo dev server, press w / a inside its window
echo.
echo Close a window or press Ctrl+C in it to stop that app.

start "Ardhang API  :8000" cmd /k ""%SELF%" api"
start "Ardhang Admin :3001" cmd /k ""%SELF%" admin"
start "Ardhang Web  :3000" cmd /k ""%SELF%" web"
if not defined SKIP_MOBILE start "Ardhang Mobile (Expo)" cmd /k ""%SELF%" mobile"

echo.
echo Launched. The first run installs dependencies per app and can take a few minutes.
exit /b 0

rem ================================== API ====================================
:run_api
title Ardhang API :8000
pushd "%ROOT%backend"
set "PY=%ROOT%backend\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [API] First run: creating .venv...
  python -m venv .venv
  if errorlevel 1 goto fail_api
)
rem Probe the install (also retries after an interrupted first run).
"%PY%" -c "import uvicorn, sqlalchemy, aiosqlite" >nul 2>nul
if errorlevel 1 (
  echo [API] Installing dependencies - first run only, this can take a few minutes...
  "%PY%" -m pip install --quiet --upgrade pip
  "%PY%" -m pip install --group dev -e .
  if errorlevel 1 goto fail_api
)
rem Local test database + CORS for the dev frontends; DEBUG off keeps logs readable.
set "DATABASE_URL=sqlite+aiosqlite:///./dev.db"
set "CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]"
set "DEBUG=false"
rem No worker/Redis locally: skip enqueueing instead of retrying (keeps requests fast).
set "ENQUEUE_JOBS=false"
rem Dev-only SUPER_ADMIN so the admin dashboard is usable locally (seed is idempotent).
set "DEV_ADMIN_EMAIL=admin@example.com"
set "DEV_ADMIN_PASSWORD=ChangeMe123!"
echo [API] Preparing SQLite database dev.db and seed data...
"%PY%" -c "import asyncio; from app.db.session import init_models; asyncio.run(init_models())"
if errorlevel 1 goto fail_api
"%PY%" -m app.seed
echo.
echo [API] FastAPI on http://localhost:8000   docs: http://localhost:8000/docs
echo [API] Admin login: admin@example.com / ChangeMe123!   (local dev SUPER_ADMIN)
echo [API] Redis not running is fine - rate limits, OTP, cache and jobs fail open.
echo.
"%PY%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
goto end

:fail_api
echo.
echo [API] Setup failed - see the messages above.
goto end

rem ================================= ADMIN ===================================
:run_admin
title Ardhang Admin :3001
pushd "%ROOT%admin"
if not exist "node_modules\next\package.json" (
  echo [Admin] First run: installing npm dependencies...
  call npm ci
  if errorlevel 1 goto fail_admin
)
set "NEXT_PUBLIC_API_URL=http://localhost:8000"
set "ADMIN_API_URL=http://localhost:8000"
rem Works around webpack/watchpack failures when the repo is on a network drive.
set "WATCHPACK_POLLING=true"
echo [Admin] Next.js on http://localhost:3001
node "node_modules\next\dist\bin\next" dev -p 3001
goto end

:fail_admin
echo.
echo [Admin] npm ci failed - see the messages above.
goto end

rem ================================== WEB ====================================
:run_web
title Ardhang Web :3000
pushd "%ROOT%web"
if not exist "node_modules\next\package.json" (
  echo [Web] First run: installing npm dependencies...
  call npm ci
  if errorlevel 1 goto fail_web
)
set "WEB_API_URL=http://localhost:8000"
set "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000"
rem Works around webpack/watchpack failures when the repo is on a network drive.
set "WATCHPACK_POLLING=true"
echo [Web] Next.js on http://localhost:3000
node "node_modules\next\dist\bin\next" dev
goto end

:fail_web
echo.
echo [Web] npm ci failed - see the messages above.
goto end

rem ================================= MOBILE ==================================
:run_mobile
title Ardhang Mobile - Expo
pushd "%ROOT%mobile"
if not exist "node_modules\expo\package.json" (
  echo [Mobile] First run: installing npm dependencies...
  call npm ci
  if errorlevel 1 goto fail_mobile
)
echo [Mobile] API base: http://10.0.2.2:8000 on Android emulator, http://localhost:8000 on web / iOS sim.
echo [Mobile] Physical device: set EXPO_PUBLIC_API_BASE_URL=http://YOUR-PC-IP:8000 before starting.
node "node_modules\expo\bin\cli" start
goto end

:fail_mobile
echo.
echo [Mobile] npm ci failed - see the messages above.
goto end

:end
endlocal
exit /b 0
