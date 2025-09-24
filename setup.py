#!/usr/bin/env python3
"""
Complete setup script for Marine Weather & AI Hazard Assistant
This script will set up the entire project from scratch
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print the project banner"""
    print("🌊" + "=" * 58 + "🌊")
    print("🌊  Marine Weather & AI Hazard Assistant - Setup  🌊")
    print("🌊" + "=" * 58 + "🌊")
    print()

def check_system():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        print("   Please run this script from the project root directory")
        return False
    print("✅ Project structure detected")
    
    return True

def install_backend_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing backend dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Backend dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install backend dependencies")
        return False

def setup_database():
    """Set up the database"""
    print("\n🗄️ Setting up database...")
    try:
        subprocess.run([sys.executable, "backend/setup_database.py"], check=True)
        print("✅ Database setup completed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Database setup failed")
        print("   Please ensure MySQL is running and accessible")
        return False

def check_node():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js {version} detected")
            return True
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found")
        return False

def install_frontend_dependencies():
    """Install frontend dependencies"""
    print("\n📦 Installing frontend dependencies...")
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    try:
        os.chdir(frontend_dir)
        subprocess.run(["npm", "install"], check=True)
        os.chdir("..")
        print("✅ Frontend dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install frontend dependencies")
        os.chdir("..")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    print("\n⚙️ Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        try:
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ .env file created from template")
            print("⚠️  Please edit .env file with your API keys and configuration")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ env.example file not found")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys:")
    print("   - OpenAI API key for AI features")
    print("   - StormGlass API key for weather data")
    print("   - Gmail SMTP credentials for email alerts")
    print()
    print("2. Start the backend server:")
    print("   python start_backend.py")
    print()
    print("3. Start the frontend (in a new terminal):")
    print("   python start_frontend.py")
    print()
    print("4. Access the application:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:8000")
    print("   API Documentation: http://localhost:8000/docs")
    print()
    print("5. Login with demo credentials:")
    print("   Email: demo@marineweather.com")
    print("   Password: demo123")
    print()
    print("🌊 Happy sailing with Marine Weather Assistant! 🌊")

def main():
    """Main setup function"""
    print_banner()
    
    # Check system requirements
    if not check_system():
        sys.exit(1)
    
    # Install backend dependencies
    if not install_backend_dependencies():
        sys.exit(1)
    
    # Set up database
    if not setup_database():
        print("⚠️  Database setup failed, but continuing...")
        print("   You can run 'python backend/setup_database.py' later")
    
    # Check Node.js
    if not check_node():
        print("⚠️  Node.js not found")
        print("   Please install Node.js 16+ from https://nodejs.org/")
        print("   Then run: python start_frontend.py")
    else:
        # Install frontend dependencies
        if not install_frontend_dependencies():
            print("⚠️  Frontend setup failed, but continuing...")
            print("   You can run 'cd frontend && npm install' later")
    
    # Create .env file
    create_env_file()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
