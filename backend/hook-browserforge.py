"""
System: Suno Automation
Module: Browserforge Hook
Purpose: Include browserforge data files in PyInstaller bundle
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('browserforge')