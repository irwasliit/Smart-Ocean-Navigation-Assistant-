@echo off
echo 🌊 Marine Weather & AI Hazard Assistant - Frontend Startup
echo ============================================================

cd frontend

echo 📦 Installing dependencies...
call npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    echo Please ensure Node.js and npm are properly installed
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully
echo.
echo 🚀 Starting React development server...
echo 📱 Frontend will be available at: http://localhost:3000
echo 🔗 Backend API should be running at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ------------------------------------------------------------

call npm run dev
