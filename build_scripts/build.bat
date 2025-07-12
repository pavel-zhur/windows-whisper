@echo off
:: Windows Whisper Build Script
:: Builds the application using PyInstaller and creates Windows installer

setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo ================================
echo Windows Whisper Build Script
echo ================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

:: Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

:: Check if NSIS is available
where makensis >nul 2>&1
if errorlevel 1 (
    echo WARNING: NSIS not found in PATH
    echo Please install NSIS from https://nsis.sourceforge.io/
    echo You can still build the executable, but the installer won't be created.
    set SKIP_INSTALLER=1
) else (
    set SKIP_INSTALLER=0
)

:: Clean previous builds
echo Cleaning previous builds...
if exist "..\dist" rmdir /s /q "..\dist"
if exist "..\build" rmdir /s /q "..\build"
if exist "WindowsWhisper-*-Setup.exe" del /q "WindowsWhisper-*-Setup.exe"

:: Install dependencies
echo Installing Python dependencies...
cd ..
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

:: Build executable with PyInstaller
echo.
echo Building executable with PyInstaller...
cd build_scripts
pyinstaller --clean --noconfirm windows-whisper.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

:: Check if executable was created
if not exist "dist\WindowsWhisper.exe" (
    echo ERROR: Executable not found after build
    pause
    exit /b 1
)

echo SUCCESS: Executable built at dist\WindowsWhisper.exe

:: Create installer if NSIS is available
if "%SKIP_INSTALLER%"=="0" (
    echo.
    echo Creating Windows installer...
    makensis installer.nsi
    if errorlevel 1 (
        echo ERROR: NSIS installer creation failed
        pause
        exit /b 1
    )
    
    :: Find the created installer
    for %%f in (WindowsWhisper-*-Setup.exe) do (
        echo SUCCESS: Installer created: %%f
        set INSTALLER_NAME=%%f
    )
    
    if defined INSTALLER_NAME (
        echo.
        echo Build completed successfully!
        echo Executable: dist\WindowsWhisper.exe
        echo Installer: !INSTALLER_NAME!
    )
) else (
    echo.
    echo Build completed successfully!
    echo Executable: dist\WindowsWhisper.exe
    echo Note: Install NSIS to create Windows installer
)

echo.
echo ================================
echo Build Summary
echo ================================
echo Executable: %CD%\dist\WindowsWhisper.exe
if "%SKIP_INSTALLER%"=="0" (
    echo Installer: %CD%\!INSTALLER_NAME!
) else (
    echo Installer: Not created (NSIS not available)
)
echo.

:: Get file size
for %%f in ("dist\WindowsWhisper.exe") do (
    set /a "size=%%~zf/1024/1024"
    echo Executable size: !size! MB
)

echo.
echo You can now test the executable by running:
echo %CD%\dist\WindowsWhisper.exe
echo.

pause