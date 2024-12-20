import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()


def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    return conn


def fetch_url_data(cursor, url_id):
    cursor.execute(
        "SELECT id, name, created_at FROM urls WHERE id = %s",
        (url_id,)
    )
    url_data = cursor.fetchone()

    if url_data is None:
        return None, None

    cursor.execute(
        "SELECT id, status_code, h1, title, description, "
        "created_at FROM url_checks WHERE url_id = %s",
        (url_id,)
    )
    checks = cursor.fetchall()
    return url_data, checks


def get_urls(cursor):
    cursor.execute("""
        SELECT u.id, u.name, uc.status_code,
        MAX(uc.created_at) AS last_check_date
        FROM urls u
        LEFT JOIN url_checks uc ON u.id = uc.url_id
        GROUP BY u.id, u.name, uc.status_code
        ORDER BY last_check_date DESC
    """)
    urls = cursor.fetchall()
    return urls


def insert_url(cursor, normalized_url):
    if is_url_added(cursor, normalized_url):
        return None

    cursor.execute(
        "INSERT INTO urls (name) VALUES (%s) RETURNING id",
        (normalized_url,)
    )
    return cursor.fetchone()[0]


def is_url_added(cursor, normalized_url):
    cursor.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_url_name(cursor, url_id):
    cursor.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
    return cursor.fetchone()


def insert_check(
        cursor,
        url_id,
        status_code,
        h1_content,
        title_content,
        description_content,
        created_at
):
    cursor.execute(
        "INSERT INTO url_checks "
        "(url_id, status_code, h1, title, description, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            url_id,
            status_code,
            h1_content,
            title_content,
            description_content,
            created_at
        )
    )
