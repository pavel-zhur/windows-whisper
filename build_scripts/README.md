# Windows Whisper Build Instructions

This directory contains scripts and configuration for building Windows installers for Windows Whisper.

## Prerequisites

### Required Software
1. **Python 3.8+** - Must be in PATH
2. **Git** (if building from source)

### For Installer Creation
3. **NSIS (Nullsoft Scriptable Install System)** - Download from https://nsis.sourceforge.io/
   - Add NSIS to PATH or install to default location

## Building Locally

### Quick Build
Run the automated build script:
```cmd
cd build_scripts
build.bat
```

This will:
- Install PyInstaller if needed
- Build the executable using PyInstaller
- Create Windows installer using NSIS (if available)

### Manual Build Steps

1. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Build executable:**
   ```cmd
   cd build_scripts
   pyinstaller --clean --noconfirm windows-whisper.spec
   ```

3. **Create installer (requires NSIS):**
   ```cmd
   makensis installer.nsi
   ```

## Build Output

- **Executable**: `../dist/WindowsWhisper.exe` (single-file, ~50-80 MB)
- **Installer**: `WindowsWhisper-0.4.0-Setup.exe` (includes auto-update, shortcuts, etc.)

## Configuration Files

### `windows-whisper.spec`
PyInstaller specification file that:
- Bundles Python runtime and all dependencies
- Creates single-file executable
- Includes resource files (profiles.yaml, .env.example)
- Optimizes for Windows GUI application

### `installer.nsi`
NSIS script that creates a professional Windows installer with:
- Windows 10/11 compatibility checks
- User-level installation (no admin required)
- Optional desktop shortcut
- Start Menu shortcuts
- Auto-start with Windows option
- Proper uninstaller with configuration preservation
- Add/Remove Programs integration

### `build.bat`
Automated build script that:
- Validates prerequisites
- Installs missing dependencies
- Builds executable and installer
- Provides build summary and file sizes

## Deployment

The generated installer (`WindowsWhisper-X.X.X-Setup.exe`) can be:
- Distributed directly to users
- Published on GitHub Releases
- Signed with code signing certificate (recommended for production)

## Troubleshooting

### Common Issues

1. **PyInstaller import errors**
   - Solution: Add missing imports to `hiddenimports` in `.spec` file

2. **Missing DLLs**
   - Solution: Check `binaries` section in `.spec` file

3. **Large executable size**
   - Solution: Add unused modules to `excludes` in `.spec` file

4. **NSIS not found**
   - Solution: Install NSIS and add to PATH, or run `makensis` from NSIS directory

### Testing

Always test the built executable on a clean Windows system without Python installed to ensure all dependencies are properly bundled.