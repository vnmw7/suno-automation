"""
System: Suno Automation
Module: Language Tags Hook
Purpose: Include language_tags data files in PyInstaller bundle
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('language_tags')