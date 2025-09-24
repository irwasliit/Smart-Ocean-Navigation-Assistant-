
#!/usr/bin/env python3
"""
Startup script for Marine Weather & AI Hazard Assistant Frontend
"""

import os
import sys
import subprocess
from pathlib import Path

def check_node_version():
    """Check if Node.js is installed and version is compatible"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js {version} detected")
        else:
            print("❌ Node.js not found")
            print("Please install Node.js 16 or higher from https://nodejs.org/")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ Node.js not found")
        print("Please install Node.js 16 or higher from https://nodejs.org/")
        sys.exit(1)

def check_npm():
    """Check if npm is available"""
    # Try different possible npm locations
    npm_paths = [
        "npm",
        "C:\\Program Files\\nodejs\\npm.cmd",
        "C:\\Program Files (x86)\\nodejs\\npm.cmd"
    ]
    
    for npm_path in npm_paths:
        try:
            result = subprocess.run([npm_path, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ npm {version} detected at {npm_path}")
                return npm_path
        except FileNotFoundError:
            continue
    
    print("❌ npm not found, trying npx...")
    return None

def check_npx():
    """Check if npx is available as fallback"""
    try:
        result = subprocess.run(["npx", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ npx {version} detected")
            return True
        else:
            print("❌ npx not found")
            return False
    except FileNotFoundError:
        print("❌ npx not found")
        return False

def install_dependencies(npm_path):
    """Install frontend dependencies if needed"""
    frontend_dir = Path(__file__).parent / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        os.chdir(frontend_dir)
        try:
            subprocess.run([npm_path, "install"], check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            sys.exit(1)
    else:
        print("✅ Frontend dependencies already installed")

def start_frontend(npm_path):
    """Start the React development server"""
    print("\n🌊 Starting Marine Weather & AI Hazard Assistant Frontend")
    print("=" * 60)
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    # Start the development server
    try:
        print("🚀 Starting React development server...")
        print("📱 Frontend will be available at: http://localhost:3000")
        print("🔗 Backend API should be running at: http://localhost:8000")
        print("\nPress Ctrl+C to stop the server")
        print("-" * 60)
        
        subprocess.run([npm_path, "run", "dev"])
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped by user")
    except Exception as e:
        print(f"❌ Error starting frontend server: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🌊 Marine Weather & AI Hazard Assistant - Frontend Startup")
    print("=" * 60)
    
    # Pre-flight checks
    check_node_version()
    
    # Check npm or npx
    npm_path = check_npm()
    if not npm_path:
        npx_available = check_npx()
        if not npx_available:
            print("❌ Neither npm nor npx found")
            print("Please reinstall Node.js from https://nodejs.org/")
            print("Make sure to check 'Add to PATH' during installation")
            sys.exit(1)
        npm_path = "npx npm"
    
    install_dependencies(npm_path)
    
    # Start the frontend
    start_frontend(npm_path)

if __name__ == "__main__":
    main()
