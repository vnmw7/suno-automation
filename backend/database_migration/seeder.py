import os
import sys
import importlib.util
from dotenv import load_dotenv

# Add the parent directory to the Python path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.supabase import get_db_connection

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def run_seeder():
    conn = get_db_connection()
    try:
        seeds_dir = os.path.join(os.path.dirname(__file__), "seeds")
        for filename in os.listdir(seeds_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                module_path = os.path.join(seeds_dir, filename)

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "insert_seeds"):
                    print(f"Seeding {module_name}...")
                    module.insert_seeds(conn)
                    print(f"Seeding {module_name} complete.")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Seeding failed: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    run_seeder()
