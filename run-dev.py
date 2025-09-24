#!/usr/bin/env python3
"""
Local development server for Eyrie Sample Manager with FastAPI
Run this to test the application without Docker
"""
import os
import sys
import subprocess

# Add the frontend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import pymongo
        print("✓ All dependencies are available")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nInstalling required packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                 "fastapi==0.104.1", "uvicorn[standard]==0.24.0", 
                                 "pymongo==4.5.0", "python-multipart==0.0.6", 
                                 "Werkzeug==2.3.7"])
            print("✓ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install dependencies")
            return False

def main():
    print("=" * 60)
    print("🚀 Eyrie Sample Manager - Local Development Server")
    print("=" * 60)
    
    if not check_dependencies():
        print("Please install dependencies manually:")
        print("pip install fastapi uvicorn pymongo python-multipart Werkzeug")
        return 1
    
    # Change to frontend directory where app.py is located
    os.chdir(os.path.join(os.path.dirname(__file__), 'frontend'))
    
    print("📍 Server URL: http://localhost:5000")
    print("🔐 Login: admin / admin")
    print("📚 API Docs: http://localhost:5000/docs")
    print("💡 Using in-memory MongoDB simulation")
    print("=" * 60)
    print("Starting server...")
    
    try:
        # Import and run the FastAPI app
        from app import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
