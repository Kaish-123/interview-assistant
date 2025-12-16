#!/usr/bin/env python3
"""
Interview Assistant - Standalone Desktop Application
A single executable that runs the complete Interview Assistant
"""
import os
import sys
import subprocess
import threading
import time
import webbrowser
import signal
from pathlib import Path

# App configuration
APP_NAME = "Interview Assistant"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000

# Get the directory where this script is located
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(os.path.dirname(sys.executable))
else:
    # Running as script
    BASE_DIR = Path(__file__).parent
    APP_DIR = BASE_DIR

BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"


class InterviewAssistantApp:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False
        
    def start_backend(self):
        """Start the FastAPI backend server"""
        print("🚀 Starting backend server...")
        
        env = os.environ.copy()
        env['PORT'] = str(BACKEND_PORT)
        env['HOST'] = '127.0.0.1'
        
        # Check for bundled backend or use Python
        backend_exe = BACKEND_DIR / ('backend.exe' if sys.platform == 'win32' else 'backend')
        
        if backend_exe.exists():
            cmd = [str(backend_exe)]
        else:
            main_py = BACKEND_DIR / 'main.py'
            python_cmd = sys.executable
            cmd = [python_cmd, str(main_py)]
        
        try:
            self.backend_process = subprocess.Popen(
                cmd,
                cwd=str(BACKEND_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Wait for backend to be ready
            for _ in range(30):
                try:
                    import urllib.request
                    urllib.request.urlopen(f'http://localhost:{BACKEND_PORT}/health', timeout=1)
                    print("✅ Backend server is ready!")
                    return True
                except:
                    time.sleep(1)
            
            print("❌ Backend server failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the Next.js frontend"""
        print("🚀 Starting frontend...")
        
        # Check if we need to start frontend or just wait for it
        try:
            import urllib.request
            urllib.request.urlopen(f'http://localhost:{FRONTEND_PORT}', timeout=1)
            print("✅ Frontend is already running!")
            return True
        except:
            pass
        
        env = os.environ.copy()
        env['PORT'] = str(FRONTEND_PORT)
        
        npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
        
        try:
            self.frontend_process = subprocess.Popen(
                [npm_cmd, 'run', 'start'],
                cwd=str(FRONTEND_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True
            )
            
            # Wait for frontend to be ready
            for _ in range(60):
                try:
                    import urllib.request
                    urllib.request.urlopen(f'http://localhost:{FRONTEND_PORT}', timeout=1)
                    print("✅ Frontend is ready!")
                    return True
                except:
                    time.sleep(1)
            
            print("❌ Frontend failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False
    
    def open_browser(self):
        """Open the app in the default browser"""
        url = f'http://localhost:{FRONTEND_PORT}'
        print(f"🌐 Opening {url} in browser...")
        webbrowser.open(url)
    
    def run_with_webview(self):
        """Run with PyWebView for native window"""
        try:
            import webview
            
            print("🖥️ Opening native window...")
            
            window = webview.create_window(
                APP_NAME,
                f'http://localhost:{FRONTEND_PORT}',
                width=1400,
                height=900,
                min_size=(800, 600),
                background_color='#0a0a0f'
            )
            
            webview.start()
            
        except ImportError:
            print("⚠️ PyWebView not installed. Opening in browser instead...")
            self.open_browser()
            self.wait_for_exit()
    
    def wait_for_exit(self):
        """Wait for user to exit"""
        print("\n" + "="*50)
        print("Interview Assistant is running!")
        print(f"Open http://localhost:{FRONTEND_PORT} in your browser")
        print("Press Ctrl+C to stop")
        print("="*50 + "\n")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
    
    def cleanup(self):
        """Clean up processes"""
        print("Cleaning up...")
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except:
                self.backend_process.kill()
        
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except:
                self.frontend_process.kill()
    
    def run(self, use_webview=True):
        """Run the application"""
        print(f"🎯 {APP_NAME} Starting...")
        print(f"📁 Base directory: {BASE_DIR}")
        
        self.running = True
        
        # Handle signals
        def signal_handler(sig, frame):
            self.running = False
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start backend
            if not self.start_backend():
                print("Failed to start backend server")
                return
            
            # Start frontend (if needed)
            # self.start_frontend()  # Uncomment if bundling frontend
            
            # Open UI
            if use_webview:
                self.run_with_webview()
            else:
                self.open_browser()
                self.wait_for_exit()
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument('--no-window', action='store_true', 
                        help='Run without native window (browser only)')
    parser.add_argument('--port', type=int, default=FRONTEND_PORT,
                        help='Frontend port')
    args = parser.parse_args()
    
    global FRONTEND_PORT
    FRONTEND_PORT = args.port
    
    app = InterviewAssistantApp()
    app.run(use_webview=not args.no_window)


if __name__ == '__main__':
    main()


