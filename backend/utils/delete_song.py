"""
Song Deletion Utility Module

This module provides reusable functionality for deleting songs both locally
and from Suno.com. It handles file cleanup and remote deletion through
browser automation.
"""

import os
import traceback
from typing import Dict, Any, Optional, List
from pathlib import Path
from camoufox.async_api import AsyncCamoufox
from configs.browser_config import config
from configs.suno_selectors import SunoSelectors
from configs.suno_selectors import SunoSelectors


class SongDeleter:
    """Handles deletion of songs from local storage and Suno.com"""
    
    def __init__(self, base_song_dir: str = "backend/songs"):
        """
        Initialize the SongDeleter.
        
        Args:
            base_song_dir (str): Base directory where songs are stored
        """
        self.base_song_dir = Path(base_song_dir)
        self.browser_config = config
        
    async def delete_song(
        self, 
        song_id: Optional[str] = None,
        file_path: Optional[str] = None,
        delete_from_suno: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a song locally and optionally from Suno.com.
        
        Args:
            song_id (Optional[str]): Suno song ID for remote deletion
            file_path (Optional[str]): Local file path to delete
            delete_from_suno (bool): Whether to delete from Suno.com
            
        Returns:
            Dict[str, Any]: Result with status and details
        """
        result = {
            "success": False,
            "local_deleted": False,
            "suno_deleted": False,
            "errors": []
        }
        
        # Delete local file if path provided
        if file_path:
            local_result = self.delete_local_file(file_path)
            result["local_deleted"] = local_result["success"]
            if not local_result["success"]:
                result["errors"].append(local_result["error"])
        
        # Delete from Suno if requested and ID provided
        if delete_from_suno and song_id:
            suno_result = await self.delete_from_suno(song_id)
            result["suno_deleted"] = suno_result["success"]
            if not suno_result["success"]:
                result["errors"].append(suno_result["error"])
        
        # Overall success if at least one deletion succeeded
        result["success"] = result["local_deleted"] or result["suno_deleted"]
        
        return result
    
    def delete_local_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete a local song file.
        
        Args:
            file_path (str): Path to the file to delete
            
        Returns:
            Dict[str, Any]: Result with success status and error if any
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            # Delete the file
            os.remove(file_path)
            print(f"[DELETE] Deleted local file: {file_path}")
            
            # Check if parent directory is empty and clean up if needed
            parent_dir = file_path.parent
            if parent_dir.exists() and not any(parent_dir.iterdir()):
                parent_dir.rmdir()
                print(f"[DELETE] Removed empty directory: {parent_dir}")
            
            return {"success": True}
            
        except Exception as e:
            error_msg = f"Failed to delete local file {file_path}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def delete_multiple_local_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Delete multiple local song files.
        
        Args:
            file_paths (List[str]): List of file paths to delete
            
        Returns:
            Dict[str, Any]: Summary of deletion results
        """
        results = {
            "total": len(file_paths),
            "deleted": 0,
            "failed": 0,
            "errors": []
        }
        
        for file_path in file_paths:
            result = self.delete_local_file(file_path)
            if result["success"]:
                results["deleted"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "file": file_path,
                    "error": result.get("error", "Unknown error")
                })
        
        return results
    
    async def delete_from_suno(self, song_id: str) -> Dict[str, Any]:
        """
        Delete a song from Suno.com using browser automation.
        
        Args:
            song_id (str): Suno song ID to delete
            
        Returns:
            Dict[str, Any]: Result with success status and error if any
        """

        SONG_URL = f"https://suno.com/song/{song_id}"

        try:
            async with AsyncCamoufox(
                headless=False,
                persistent_context=True,
                user_data_dir="backend/camoufox_session_data",
                os=("windows"),
                config=self.browser_config,
                humanize=True,
                i_know_what_im_doing=True,
            ) as browser:
                page = await browser.new_page()
                
                try:
                    print(f"[NAVIGATE] Navigating to song: {SONG_URL}")
                    await page.goto(SONG_URL)
                    await page.wait_for_load_state("domcontentloaded", timeout=30000)
                    
                    # Look for the options/menu button (usually three dots)
                    options_button = await self._find_options_button(page)
                    if not options_button:
                        return {
                            "success": False,
                            "error": "Could not find options button on song page"
                        }
                    
                    await options_button.click()
                    await page.wait_for_timeout(1000)
                    
                    # Look for delete/trash option in the menu
                    delete_button = await self._find_delete_button(page)
                    if not delete_button:
                        return {
                            "success": False,
                            "error": "Could not find delete option in menu"
                        }
                    
                    await delete_button.click()
                    await page.wait_for_timeout(2000)
                    
                    print(f"[DELETE] Successfully deleted song {song_id} from Suno.com")
                    return {"success": True}
                    
                except Exception as e:
                    error_msg = f"Failed to delete from Suno: {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    traceback.print_exc()
                    return {
                        "success": False,
                        "error": error_msg
                    }
                finally:
                    await page.close()
                    
        except Exception as e:
            error_msg = f"Browser automation error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    async def _find_options_button(self, page):
        """Find the options/menu button on the song page."""
        selectors = SunoSelectors.OPTIONS_BUTTON.get("selectors", [])

        for selector in selectors:
            try:
                button = page.locator(selector).first
                if await button.is_visible(timeout=2000):
                    return button
            except Exception:
                continue
        return None
    
    async def _find_delete_button(self, page):
        """Find the delete button in the options menu."""
        selectors = SunoSelectors.DELETE_BUTTON.get("selectors", [])

        for selector in selectors:
            try:
                button = page.locator(selector).first
                if await button.is_visible(timeout=2000):
                    return button
            except Exception:
                continue
        return None
    
    
    def find_songs_in_directory(self, directory: str, pattern: str = "*.mp3") -> List[str]:
        """
        Find all song files in a directory matching a pattern.
        
        Args:
            directory (str): Directory to search
            pattern (str): File pattern to match (default: "*.mp3")
            
        Returns:
            List[str]: List of file paths found
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        
        return [str(f) for f in dir_path.glob(pattern) if f.is_file()]


# Convenience function for simple deletion
async def delete_song(
    song_id: Optional[str] = None,
    file_path: Optional[str] = None,
    delete_from_suno: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to delete a song without instantiating the class.
    
    Args:
        song_id (Optional[str]): Suno song ID for remote deletion
        file_path (Optional[str]): Local file path to delete
        delete_from_suno (bool): Whether to delete from Suno.com
        
    Returns:
        Dict[str, Any]: Result with status and details
    """
    deleter = SongDeleter()
    return await deleter.delete_song(song_id, file_path, delete_from_suno)


# Convenience function for batch local deletion
def delete_local_songs(file_paths: List[str]) -> Dict[str, Any]:
    """
    Convenience function to delete multiple local song files.
    
    Args:
        file_paths (List[str]): List of file paths to delete
        
    Returns:
        Dict[str, Any]: Summary of deletion results
    """
    deleter = SongDeleter()
    return deleter.delete_multiple_local_files(file_paths)