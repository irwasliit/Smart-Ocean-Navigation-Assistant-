#!/usr/bin/env python3
"""
Startup script for Marine Weather & AI Hazard Assistant Backend
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi  
        import uvicorn
        import sqlalchemy  
        import mysql 
        print("✅ Required dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

def check_database():
    """Check if database is accessible"""
    try:
        from backend.database import engine
        engine.connect()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please ensure MySQL is running and database is set up")
        print("Run: python backend/setup_database.py")
        sys.exit(1)

def start_server():
    """Start the FastAPI server"""
    print("\n🌊 Starting Marine Weather & AI Hazard Assistant Backend")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Start the server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--timeout-keep-alive", "150",
            "--timeout-graceful-shutdown", "150",
            "--log-level", "info",
            "--no-access-log"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🌊 Marine Weather & AI Hazard Assistant - Backend Startup")
    print("=" * 60)
    
    # Pre-flight checks
    check_python_version()
    check_dependencies()
    check_database()
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
