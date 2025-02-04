import psycopg2
import os
from dotenv import load_dotenv

def test_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        print("Connection successful!")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {str(e)}")

test_connection()
