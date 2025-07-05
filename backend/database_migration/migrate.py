import os
import sys
import importlib.util
import psycopg2
from dotenv import load_dotenv

# Add the parent directory to the Python path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def get_db_connection():
    """Establishes a connection to the database using credentials from environment variables for the session pooler."""
    try:
        # Load individual connection parameters from environment variables
        db_user = os.getenv("USER")
        db_password = os.getenv("PASSWORD")
        db_host = os.getenv("HOST")
        db_port = os.getenv("PORT")
        db_name = os.getenv("DBNAME")

        # Check if all required environment variables are set
        required_vars = {"USER": db_user, "PASSWORD": db_password, "HOST": db_host, "PORT": db_port, "DBNAME": db_name}
        missing_vars = [key for key, value in required_vars.items() if not value]

        if missing_vars:
            print(f"Error: The following environment variables are not set: {', '.join(missing_vars)}")
            sys.exit(1)
        
        # Establish the connection using the individual parameters
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)


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
