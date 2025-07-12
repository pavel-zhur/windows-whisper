# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files

# Get the directory containing this spec file and add project root to Python path
spec_dir = os.path.dirname(SPECPATH)
sys.path.insert(0, spec_dir)

# Collect data files (relative to project root)
datas = [
    (os.path.join(spec_dir, 'profiles.yaml'), '.'),
    (os.path.join(spec_dir, '.env.example'), '.'),
    (os.path.join(spec_dir, 'README.md'), '.'),
    (os.path.join(spec_dir, 'LICENSE'), '.'),
]

# Collect PyQt5 data files
datas += collect_data_files('PyQt5')

# Hidden imports for PyQt5 and other dependencies
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'keyboard',
    'pyaudio',
    'pyperclip',
    'numpy',
    'yaml',
    'dotenv',
    'requests',
    'src.audio',
    'src.auto_type',
    'src.profile_manager',
    'src.profile_switching_hotkey',
    'src.translation',
    'src.ui.overlay',
    'src.utils',
    'src.whisper_api',
]

# Excluded modules to reduce size
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'pandas',
    'PIL',
    'unittest',
    'test',
    'distutils',
    'setuptools',
]

# Analysis
a = Analysis(
    [os.path.join(spec_dir, 'main.py')],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WindowsWhisper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windows GUI app, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Add icon file if available
    version_info=None,  # TODO: Add version info
)