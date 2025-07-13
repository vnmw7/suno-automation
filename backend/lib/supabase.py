import os
import sys
import psycopg2

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


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
        required_vars = {
            "USER": db_user,
            "PASSWORD": db_password,
            "HOST": db_host,
            "PORT": db_port,
            "DBNAME": db_name,
        }
        missing_vars = [key for key, value in required_vars.items() if not value]

        if missing_vars:
            print(
                f"Error: The following environment variables are not set: {', '.join(missing_vars)}"
            )
            sys.exit(1)

        # Establish the connection using the individual parameters
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)


def main():
    conn = get_db_connection()
    if conn:
        print("Database connection successful!")
        conn.close()


if __name__ == "__main__":
    main()
