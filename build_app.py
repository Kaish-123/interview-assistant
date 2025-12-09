#!/usr/bin/env python3
"""
Build Script for Interview Assistant Desktop Application
Creates distributable packages for Mac (.app, .dmg) and Windows (.exe)
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Configuration
APP_NAME = "Interview Assistant"
APP_VERSION = "1.0.0"
APP_BUNDLE_ID = "co.techyera.interview-assistant"
APP_AUTHOR = "TechYera"

# Paths
BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
BUILD_DIR = BASE_DIR / "build"
DIST_DIR = BASE_DIR / "dist"


def run_command(cmd, cwd=None, env=None):
    """Run a command and print output"""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env or os.environ,
        shell=isinstance(cmd, str),
        capture_output=True,
        text=True
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise Exception(f"Command failed with code {result.returncode}")
    return result


def install_dependencies():
    """Install required Python packages for building"""
    print("\n📦 Installing build dependencies...")
    packages = [
        "pyinstaller",
        "pywebview",
        "pillow",  # For icon generation
    ]
    for pkg in packages:
        try:
            run_command([sys.executable, "-m", "pip", "install", pkg, "-q"])
        except:
            pass


def build_backend():
    """Build the backend as a standalone executable"""
    print("\n🔧 Building backend...")
    
    # Change to backend directory
    os.chdir(BACKEND_DIR)
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--name", "backend",
        "--clean",
        "--noconfirm",
        # Add data files
        "--add-data", f"database{os.pathsep}database",
        "--add-data", f"services{os.pathsep}services",
        "--add-data", f"routes{os.pathsep}routes",
        "--add-data", f"models{os.pathsep}models",
        # Hidden imports
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "openai",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        "--hidden-import", "pydantic",
        "--hidden-import", "websockets",
        "--hidden-import", "aiofiles",
        "--hidden-import", "httpx",
        "--collect-all", "openai",
        "--collect-all", "sqlalchemy",
        "--collect-all", "pydantic",
        "main.py"
    ]
    
    run_command(cmd)
    
    # Move dist to main dist folder
    backend_dist = BACKEND_DIR / "dist" / "backend"
    if backend_dist.exists():
        target = DIST_DIR / "backend"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(backend_dist, target)
        print(f"✅ Backend built: {target}")


def build_frontend():
    """Build the Next.js frontend"""
    print("\n🔧 Building frontend...")
    
    os.chdir(FRONTEND_DIR)
    
    # Install dependencies
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    run_command([npm_cmd, "install"])
    
    # Build
    run_command([npm_cmd, "run", "build"])
    
    # Copy build output
    frontend_build = FRONTEND_DIR / ".next"
    if frontend_build.exists():
        target = DIST_DIR / "frontend"
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        
        # Copy necessary files
        shutil.copytree(frontend_build, target / ".next")
        shutil.copytree(FRONTEND_DIR / "public", target / "public")
        shutil.copy(FRONTEND_DIR / "package.json", target / "package.json")
        shutil.copy(FRONTEND_DIR / "next.config.js", target / "next.config.js")
        
        print(f"✅ Frontend built: {target}")


def build_standalone_app():
    """Build the standalone desktop application"""
    print("\n🔧 Building standalone application...")
    
    os.chdir(BASE_DIR)
    
    # Determine icon file
    if platform.system() == "Darwin":
        icon_file = BASE_DIR / "resources" / "icon.icns"
    elif platform.system() == "Windows":
        icon_file = BASE_DIR / "resources" / "icon.ico"
    else:
        icon_file = None
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", APP_NAME.replace(" ", ""),
        "--clean",
        "--noconfirm",
        "--windowed",  # No console window
        # Add the backend and frontend
        "--add-data", f"backend{os.pathsep}backend",
        "--add-data", f"frontend{os.pathsep}frontend",
        # Hidden imports for the launcher
        "--hidden-import", "webview",
        "--hidden-import", "urllib.request",
    ]
    
    if icon_file and icon_file.exists():
        cmd.extend(["--icon", str(icon_file)])
    
    cmd.append("standalone_app.py")
    
    run_command(cmd)
    print("✅ Standalone app built!")


def create_mac_app():
    """Create macOS .app bundle and .dmg"""
    if platform.system() != "Darwin":
        print("⚠️ Skipping macOS build (not on macOS)")
        return
    
    print("\n🍎 Creating macOS application...")
    
    # The PyInstaller already creates a .app on macOS
    app_path = DIST_DIR / f"{APP_NAME.replace(' ', '')}.app"
    
    if app_path.exists():
        print(f"✅ macOS app created: {app_path}")
        
        # Create DMG
        print("Creating DMG installer...")
        dmg_path = DIST_DIR / f"{APP_NAME.replace(' ', '')}-{APP_VERSION}.dmg"
        
        try:
            # Use create-dmg if available
            run_command([
                "create-dmg",
                "--volname", APP_NAME,
                "--window-size", "600", "400",
                "--icon-size", "100",
                "--app-drop-link", "450", "200",
                str(dmg_path),
                str(app_path)
            ])
        except:
            # Fallback: Use hdiutil
            run_command([
                "hdiutil", "create",
                "-volname", APP_NAME,
                "-srcfolder", str(app_path),
                "-ov",
                "-format", "UDZO",
                str(dmg_path)
            ])
        
        if dmg_path.exists():
            print(f"✅ DMG created: {dmg_path}")


def create_windows_installer():
    """Create Windows .exe installer"""
    if platform.system() != "Windows":
        print("⚠️ Skipping Windows build (not on Windows)")
        return
    
    print("\n🪟 Creating Windows installer...")
    
    exe_path = DIST_DIR / f"{APP_NAME.replace(' ', '')}.exe"
    
    if exe_path.exists():
        print(f"✅ Windows executable created: {exe_path}")
        
        # Could use NSIS or Inno Setup here for a proper installer
        # For now, the standalone .exe is sufficient


def create_release_package():
    """Create release package with all necessary files"""
    print("\n📦 Creating release package...")
    
    release_dir = DIST_DIR / f"InterviewAssistant-{APP_VERSION}-{platform.system().lower()}"
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    exe_name = f"{APP_NAME.replace(' ', '')}"
    if platform.system() == "Windows":
        exe_name += ".exe"
    elif platform.system() == "Darwin":
        exe_name += ".app"
    
    src_exe = DIST_DIR / exe_name
    if src_exe.exists():
        if src_exe.is_dir():
            shutil.copytree(src_exe, release_dir / exe_name)
        else:
            shutil.copy(src_exe, release_dir / exe_name)
    
    # Copy README
    readme_content = f"""# {APP_NAME}

AI-powered interview preparation tool with real-time transcription.

## Installation

### macOS
1. Drag "{exe_name}" to your Applications folder
2. Right-click and select "Open" the first time (to bypass Gatekeeper)
3. Grant microphone and accessibility permissions when prompted

### Windows
1. Run "{exe_name}"
2. Allow the app through Windows Firewall if prompted
3. Grant microphone permissions when prompted

## Usage

1. Start the application
2. Upload your resume and job description
3. Press ` (backtick) to start/stop recording
4. The AI will transcribe and help you answer interview questions

## Keyboard Shortcuts

- ` (backtick) - Start/Stop recording
- Page Down - Scroll to bottom
- Page Up - Scroll to top
- F2 - Save UI layout
- Escape - Cancel action

## Support

Website: https://techyera.co
Email: support@techyera.co

Version: {APP_VERSION}
"""
    
    (release_dir / "README.md").write_text(readme_content)
    
    # Create zip
    zip_path = DIST_DIR / f"InterviewAssistant-{APP_VERSION}-{platform.system().lower()}"
    shutil.make_archive(str(zip_path), 'zip', release_dir)
    
    print(f"✅ Release package created: {zip_path}.zip")


def main():
    """Main build process"""
    print("=" * 60)
    print(f"Building {APP_NAME} v{APP_VERSION}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print("=" * 60)
    
    # Create directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    
    try:
        # Install dependencies
        install_dependencies()
        
        # Build components
        build_backend()
        build_frontend()
        build_standalone_app()
        
        # Create platform-specific packages
        if platform.system() == "Darwin":
            create_mac_app()
        elif platform.system() == "Windows":
            create_windows_installer()
        
        # Create release package
        create_release_package()
        
        print("\n" + "=" * 60)
        print("✅ BUILD COMPLETE!")
        print(f"Output directory: {DIST_DIR}")
        print("=" * 60)
        
        # List output files
        print("\nOutput files:")
        for f in DIST_DIR.iterdir():
            size = f.stat().st_size / (1024 * 1024)  # MB
            print(f"  - {f.name} ({size:.1f} MB)")
            
    except Exception as e:
        print(f"\n❌ BUILD FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

