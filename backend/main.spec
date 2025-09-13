"""
System: Suno Automation
Module: PyInstaller Spec
Purpose: Bundle backend application with all dependencies including Camoufox browser
"""

# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path
import site

block_cipher = None

# Add backend directory to path
backend_dir = Path('.').resolve()
sys.path.insert(0, str(backend_dir))

# Find site-packages directory
site_packages = site.getsitepackages()[0]
if not os.path.exists(site_packages):
    # Try virtual environment - check common venv locations
    venv_path = backend_dir / '.venv' / 'Lib' / 'site-packages'
    if venv_path.exists():
        site_packages = venv_path
    else:
        site_packages = backend_dir / 'venv' / 'Lib' / 'site-packages'
else:
    site_packages = Path(site_packages)

# Collect data files for packages that need them
extra_datas = []

# Browserforge data files
browserforge_path = Path(site_packages) / 'browserforge'
if browserforge_path.exists():
    for data_dir in ['headers/data', 'fingerprints/data']:
        src = browserforge_path / data_dir
        if src.exists():
            dst = f'browserforge/{data_dir}'
            extra_datas.append((str(src), dst))

# Language tags data files
language_tags_path = Path(site_packages) / 'language_tags'
if language_tags_path.exists():
    data_path = language_tags_path / 'data'
    if data_path.exists():
        extra_datas.append((str(data_path), 'language_tags/data'))

a = Analysis(
    ['main.py'],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=[item for item in [
        # Include .env file if exists
        ('.env', '.') if os.path.exists('.env') else ('.env.sample', '.env'),
        # Include all API modules
        ('api', 'api'),
        # Include routes
        ('routes', 'routes'),
        # Include services
        ('services', 'services'),
        # Include utils
        ('utils', 'utils'),
        # Include lib
        ('lib', 'lib'),
        # Include config
        ('config', 'config'),
        # Include constants
        ('constants', 'constants'),
        # Include songs directory
        ('songs', 'songs'),
        # Include logs directory structure
        ('logs', 'logs'),
        # Include camoufox session data directory if exists
        ('camoufox_session_data', 'camoufox_session_data') if os.path.exists('camoufox_session_data') else None,
    ] if item is not None] + extra_datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'nodriver',
        'selenium_driverless',
        'openai',
        'browserforge',
        'camoufox',
        'camoufox.sync_api',
        'camoufox.async_api',
        'python-dotenv',
        'pythonbible',
        'supabase',
        'pandas',
        'psycopg2',
        'python-slugify',
        'google-adk',
        # Add any additional hidden imports for your routes
        'api.song.routes',
        'api.ai_review.routes',
        'api.ai_generation.routes',
        'api.orchestrator.routes',
        'routes.songs',
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[
        'test',
        'tests',
        'pytest',
        'lab',
        'database_migration',
        'multi_tool_agent',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='suno-automation-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='suno-automation-backend',
)