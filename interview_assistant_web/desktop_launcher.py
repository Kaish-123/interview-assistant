#!/usr/bin/env python3
"""
Interview Assistant Desktop Launcher
Starts the backend server and opens the frontend in browser
"""

import os
import sys
import time
import signal
import subprocess
import webbrowser
import threading
from pathlib import Path

# Get the directory where this script is located
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(os.path.dirname(sys.executable))
else:
    # Running as script
    BASE_DIR = Path(__file__).parent
    APP_DIR = BASE_DIR

BACKEND_DIR = BASE_DIR / 'backend'
FRONTEND_DIR = BASE_DIR / 'frontend' / 'out'  # Static export directory
BACKEND_PORT = 8000
FRONTEND_PORT = 3000

backend_process = None
frontend_process = None


def find_free_port(start_port):
    """Find a free port starting from start_port"""
    import socket
    port = start_port
    while port < start_port + 100:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            port += 1
    return start_port


def start_backend():
    """Start the FastAPI backend server"""
    global backend_process
    
    # Change to backend directory
    os.chdir(BACKEND_DIR)
    
    # Add backend to path
    sys.path.insert(0, str(BACKEND_DIR))
    
    env = os.environ.copy()
    env['PYTHONPATH'] = str(BACKEND_DIR)
    
    # Start uvicorn
    backend_process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', str(BACKEND_PORT)],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"✅ Backend started on port {BACKEND_PORT}")
    return backend_process


def start_frontend_server():
    """Start a simple HTTP server to serve the static frontend"""
    global frontend_process
    
    if not FRONTEND_DIR.exists():
        print(f"⚠️ Frontend build not found at {FRONTEND_DIR}")
        print("Opening backend API docs instead...")
        return None
    
    # Use Python's built-in HTTP server
    frontend_process = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(FRONTEND_PORT), '--directory', str(FRONTEND_DIR)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"✅ Frontend started on port {FRONTEND_PORT}")
    return frontend_process


def wait_for_server(port, timeout=30):
    """Wait for a server to be ready"""
    import socket
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(0.5)
    return False


def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    global backend_process, frontend_process
    
    print("\n🛑 Shutting down...")
    
    if backend_process:
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except:
            backend_process.kill()
    
    if frontend_process:
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5)
        except:
            frontend_process.kill()
    
    print("👋 Goodbye!")
    sys.exit(0)


def main():
    """Main entry point"""
    print("🚀 Starting Interview Assistant...")
    print(f"📂 Base directory: {BASE_DIR}")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Start backend
    print("⏳ Starting backend server...")
    start_backend()
    
    # Wait for backend to be ready
    if not wait_for_server(BACKEND_PORT, timeout=30):
        print("❌ Backend failed to start!")
        cleanup()
        return
    
    print("✅ Backend is ready!")
    
    # Start frontend server (if available)
    print("⏳ Starting frontend server...")
    start_frontend_server()
    
    # Determine which URL to open
    if FRONTEND_DIR.exists():
        # Wait for frontend to be ready
        if wait_for_server(FRONTEND_PORT, timeout=10):
            url = f"http://localhost:{FRONTEND_PORT}"
            print(f"✅ Frontend is ready!")
        else:
            url = f"http://localhost:{BACKEND_PORT}/docs"
            print("⚠️ Frontend not ready, opening API docs")
    else:
        # No frontend build, point to dev server or API docs
        url = f"http://localhost:{BACKEND_PORT}/docs"
        print("ℹ️ No frontend build found. For full UI, run 'npm run dev' in frontend/")
    
    # Open browser
    print(f"🌐 Opening {url} in your browser...")
    time.sleep(1)
    webbrowser.open(url)
    
    print("\n" + "="*50)
    print("🎯 Interview Assistant is running!")
    print(f"   Backend:  http://localhost:{BACKEND_PORT}")
    if FRONTEND_DIR.exists():
        print(f"   Frontend: http://localhost:{FRONTEND_PORT}")
    print("="*50)
    print("\nPress Ctrl+C to stop the server...\n")
    
    # Keep running until interrupted
    try:
        while True:
            # Check if processes are still running
            if backend_process and backend_process.poll() is not None:
                print("❌ Backend process died!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == '__main__':
    main()


