#!/usr/bin/env python3
"""
Quick launcher for PassPrint localhost server
"""

import subprocess
import sys
import os

def check_python():
    """Check if Python is available"""
    try:
        subprocess.run([sys.executable, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    print("🔍 Checking Python installation...")
    if not check_python():
        print("❌ Python is not installed or not in PATH")
        print("📥 Please install Python from: https://python.org")
        print("   Make sure to check 'Add Python to PATH' during installation")
        input("Press Enter to exit...")
        return

    print("✅ Python found!")
    print("🚀 Starting PassPrint server...")

    # Run the server
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run([sys.executable, "server.py"])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()