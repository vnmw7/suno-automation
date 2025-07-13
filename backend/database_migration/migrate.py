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


def migrate():
    """Runs database migrations to create tables."""
    conn = get_db_connection()
    try:
        tables_dir = os.path.join(os.path.dirname(__file__), "tables")
        for filename in sorted(os.listdir(tables_dir)):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                module_path = os.path.join(tables_dir, filename)

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                print(f"Creating table for {module.TABLE_NAME}...")
                module.create_table(conn)

        conn.commit()
        print("Table creation completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Table creation failed: {e}")
    finally:
        conn.close()


def main():
    """Main function to run the database migrations."""
    migrate()


if __name__ == "__main__":
    main()
