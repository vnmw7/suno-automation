"""
System: Suno Automation
Module: Camoufox Hook
Purpose: Include camoufox data files in PyInstaller bundle
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files('camoufox')
hiddenimports = collect_submodules('camoufox')