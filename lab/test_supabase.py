import importlib
import importlib.util
import os

lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib"))
supabase_utils_path = os.path.join(lib_path, "supabase.py")

spec = importlib.util.spec_from_file_location("supabase_utils", supabase_utils_path)
supabase_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supabase_utils)

supabase = supabase_utils.supabase

response = (
    supabase.table("bible_verses_tbl")
    .select("verse_text")
    .eq("book", "ACT")
    .eq("chapter", 10)
    .eq("start_verse", 1)
    .limit(1)
    .execute()
)
print(response.data[0]["verse_text"] if response.data else None)
