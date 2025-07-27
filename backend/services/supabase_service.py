import sys
import os
from typing import Dict, List, Optional

# Add the parent directory to the path to import from lib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.supabase import get_db_connection


class SupabaseService:
    """Service class for database operations with song_structure_tbl and tblprogress_v1"""

    def __init__(self):
        self.connection = None

    def get_connection(self):
        """Get database connection"""
        if not self.connection or self.connection.closed:
            self.connection = get_db_connection()
        return self.connection

    def get_song_structure_by_id(self, structure_id: int) -> Optional[Dict]:
        """
        Retrieve song structure data by ID from song_structure_tbl
        
        Args:
            structure_id (int): The ID of the song structure
            
        Returns:
            Optional[Dict]: Song structure data or None if not found
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                id,
                book_name,
                chapter,
                verse_range,
                song_structure,
                tone,
                styles
            FROM song_structure_tbl 
            WHERE id = %s
            """
            
            cursor.execute(query, (structure_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'book_name': result[1],
                    'chapter': result[2],
                    'verse_range': result[3],
                    'song_structure': result[4],
                    'tone': result[5],
                    'styles': result[6]
                }
            return None
            
        except Exception as e:
            print(f"Error retrieving song structure by ID {structure_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def get_lyrics_by_song_struct_id(self, song_struct_id: int) -> List[Dict]:
        """
        Retrieve lyrics data from tblprogress_v1 by song_struct_id
        
        Args:
            song_struct_id (int): The song structure ID to filter by
            
        Returns:
            List[Dict]: List of lyrics data matching the song_struct_id
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                pg1_id,
                pg1_created_at,
                pg1_song_struct_id,
                pg1_style,
                pg1_lyrics,
                pg1_song_id,
                pg1_status,
                pg1_reviews,
                pg1_updated_at
            FROM tblprogress_v1 
            WHERE pg1_song_struct_id = %s
            ORDER BY pg1_created_at DESC
            """
            
            cursor.execute(query, (song_struct_id,))
            results = cursor.fetchall()
            
            lyrics_data = []
            for result in results:
                lyrics_data.append({
                    'pg1_id': result[0],
                    'pg1_created_at': result[1],
                    'pg1_song_struct_id': result[2],
                    'pg1_style': result[3],
                    'pg1_lyrics': result[4],
                    'pg1_song_id': result[5],
                    'pg1_status': result[6],
                    'pg1_reviews': result[7],
                    'pg1_updated_at': result[8]
                })
            
            return lyrics_data
            
        except Exception as e:
            print(f"Error retrieving lyrics by song_struct_id {song_struct_id}: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_song_with_lyrics(self, structure_id: int) -> Optional[Dict]:
        """
        Retrieve combined song structure and lyrics data by structure ID
        
        Args:
            structure_id (int): The song structure ID
            
        Returns:
            Optional[Dict]: Combined data with song structure and associated lyrics
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Join query to get both song structure and lyrics data
            query = """
            SELECT 
                s.id,
                s.book_name,
                s.chapter,
                s.verse_range,
                s.song_structure,
                s.tone,
                s.styles,
                p.pg1_id,
                p.pg1_created_at,
                p.pg1_style,
                p.pg1_lyrics,
                p.pg1_song_id,
                p.pg1_status,
                p.pg1_reviews,
                p.pg1_updated_at
            FROM song_structure_tbl s
            LEFT JOIN tblprogress_v1 p ON s.id = p.pg1_song_struct_id
            WHERE s.id = %s
            ORDER BY p.pg1_created_at DESC
            """
            
            cursor.execute(query, (structure_id,))
            results = cursor.fetchall()
            
            if not results:
                return None
            
            # Structure the data
            song_data = None
            lyrics_list = []
            
            for result in results:
                # Song structure data (same for all rows)
                if song_data is None:
                    song_data = {
                        'id': result[0],
                        'book_name': result[1],
                        'chapter': result[2],
                        'verse_range': result[3],
                        'song_structure': result[4],
                        'tone': result[5],
                        'styles': result[6]
                    }
                
                # Lyrics data (multiple rows possible)
                if result[7] is not None:  # pg1_id exists
                    lyrics_list.append({
                        'pg1_id': result[7],
                        'pg1_created_at': result[8],
                        'pg1_style': result[9],
                        'pg1_lyrics': result[10],
                        'pg1_song_id': result[11],
                        'pg1_status': result[12],
                        'pg1_reviews': result[13],
                        'pg1_updated_at': result[14]
                    })
            
            return {
                'song_structure': song_data,
                'lyrics': lyrics_list
            }
            
        except Exception as e:
            print(f"Error retrieving combined song data for ID {structure_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def delete_song(self, song_structure_id: int) -> bool:
        """
        Deletes the song entry from tblprogress_v1 by song_structure_id.

        Args:
            song_structure_id (int): The song structure ID to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        # TODO: Consider adding transaction handling for atomic operations
        # TODO: Should we also delete from song_structure_tbl to avoid orphaned structures?
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = "DELETE FROM tblprogress_v1 WHERE pg1_song_struct_id = %s"
            cursor.execute(query, (song_structure_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting song with structure_id {song_structure_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_all_song_structures(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Retrieve all song structures with pagination
        
        Args:
            limit (int): Maximum number of records to return
            offset (int): Number of records to skip
            
        Returns:
            List[Dict]: List of song structure data
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                id,
                book_name,
                chapter,
                verse_range,
                song_structure,
                tone,
                styles
            FROM song_structure_tbl 
            ORDER BY id
            LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (limit, offset))
            results = cursor.fetchall()
            
            structures = []
            for result in results:
                structures.append({
                    'id': result[0],
                    'book_name': result[1],
                    'chapter': result[2],
                    'verse_range': result[3],
                    'song_structure': result[4],
                    'tone': result[5],
                    'styles': result[6]
                })
            
            return structures
            
        except Exception as e:
            print(f"Error retrieving all song structures: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def close_connection(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def __del__(self):
        """Destructor to ensure connection is closed"""
        self.close_connection()


# Convenience functions for direct use
def get_song_structure_by_id(structure_id: int) -> Optional[Dict]:
    """
    Convenience function to get song structure by ID
    
    Args:
        structure_id (int): The ID of the song structure
        
    Returns:
        Optional[Dict]: Song structure data or None if not found
    """
    service = SupabaseService()
    try:
        return service.get_song_structure_by_id(structure_id)
    finally:
        service.close_connection()


def get_lyrics_by_song_struct_id(song_struct_id: int) -> List[Dict]:
    """
    Convenience function to get lyrics by song structure ID
    
    Args:
        song_struct_id (int): The song structure ID to filter by
        
    Returns:
        List[Dict]: List of lyrics data
    """
    service = SupabaseService()
    try:
        return service.get_lyrics_by_song_struct_id(song_struct_id)
    finally:
        service.close_connection()


def get_song_with_lyrics(structure_id: int) -> Optional[Dict]:
    """
    Convenience function to get combined song structure and lyrics data
    
    Args:
        structure_id (int): The song structure ID
        
    Returns:
        Optional[Dict]: Combined data with song structure and associated lyrics
    """
    service = SupabaseService()
    try:
        return service.get_song_with_lyrics(structure_id)
    finally:
        service.close_connection()


if __name__ == "__main__":
    # Test the functions
    print("Testing SupabaseService...")
    
    service = SupabaseService()
    
    # Test getting song structure by ID (assuming ID 1 exists)
    print("\n1. Testing get_song_structure_by_id(1):")
    structure = service.get_song_structure_by_id(1)
    if structure:
        print(f"Found structure: {structure}")
    else:
        print("No structure found with ID 1")
    
    # Test getting lyrics by song_struct_id (assuming structure exists)
    if structure:
        print(f"\n2. Testing get_lyrics_by_song_struct_id({structure['id']}):")
        lyrics = service.get_lyrics_by_song_struct_id(structure['id'])
        print(f"Found {len(lyrics)} lyrics entries")
        for lyric in lyrics:
            print(f"  - Lyric ID: {lyric['pg1_id']}, Status: {lyric['pg1_status']}")
    
    # Test getting combined data
    print("\n3. Testing get_song_with_lyrics(1):")
    combined = service.get_song_with_lyrics(1)
    if combined:
        print("Combined data found:")
        print(f"  - Structure: {combined['song_structure']['book_name']} {combined['song_structure']['chapter']}:{combined['song_structure']['verse_range']}")
        print(f"  - Lyrics count: {len(combined['lyrics'])}")
    else:
        print("No combined data found")
    
    service.close_connection()
