# reset_rds.py
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get RDS connection details from environment
DB_PARAMS = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def reset_database():
    try:
        # Connect to the database
        print("Connecting to RDS...")
        conn = psycopg2.connect(**DB_PARAMS)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Drop all tables in the public schema
        print("Dropping existing schema...")
        cur.execute("""
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            GRANT ALL ON SCHEMA public TO postgres;
            GRANT ALL ON SCHEMA public TO public;
        """)
        
        print("Existing schema dropped successfully!")
        
        # Read and execute init.sql
        print("Initializing new schema...")
        with open('init.sql', 'r') as file:
            init_sql = file.read()
            cur.execute(init_sql)
            
        print("Database reset and reinitialized successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    confirmation = input("This will delete all data in the RDS database. Are you sure? (yes/no): ")
    if confirmation.lower() == 'yes':
        reset_database()
    else:
        print("Operation cancelled.")