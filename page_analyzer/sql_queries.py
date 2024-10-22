import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()


def get_db_connection():
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise


def execute_sql_file(filename):
    with open(filename, 'r') as file:
        sql_script = file.read()

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_script)
            conn.commit()


if __name__ == '__main__':
    sql_file_path = os.getenv('SQL_FILE_PATH')
    if not sql_file_path:
        raise ValueError("SQL_FILE_PATH environment variable is not set.")
    execute_sql_file(sql_file_path)
