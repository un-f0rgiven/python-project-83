from flask import (Flask,
                   render_template,
                   redirect,
                   url_for,
                   request,
                   flash,
                   get_flashed_messages)
import os
import psycopg2
import logging
from dotenv import load_dotenv
from datetime import date
from functools import wraps
from page_analyzer.parser import parse_html
from page_analyzer.urls import is_valid_url, normalize_url
from page_analyzer.requests import fetch_url
from page_analyzer.sql_queries import (fetch_url_data,
                                       get_urls,
                                       insert_url,
                                       is_url_added,
                                       get_url_name,
                                       insert_check)


load_dotenv()

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')
app.config['DEBUG'] = True


def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    return conn


def init_cursor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                return func(cursor, conn, *args, **kwargs)

    return wrapper


@app.route('/', methods=['GET'])
def get_index():
    return render_template('index.html')


@app.route('/urls/<int:url_id>')
@init_cursor
def show_url(cursor, conn, url_id):
    flashed_messages = get_flashed_messages(with_categories=True)

    url_data, checks = fetch_url_data(cursor, url_id)

    if url_data is None:
        flash('URL не найден.', 'danger')
        return render_template('index.html', url_data=url_data), 404

    return render_template(
        'show_url.html',
        url_id=url_data[0],
        url_name=url_data[1],
        created_at=url_data[2],
        checks=checks,
        flashed_messages=flashed_messages
    )


@app.get('/urls')
@init_cursor
def handle_get_request(cursor, conn):
    urls = get_urls(cursor)
    return render_template('list_urls.html', urls=urls)


@app.post('/urls')
@init_cursor
def handle_post_request(cursor, conn):
    url = request.form.get('url')

    if not is_valid_url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html', url=url), 422

    normalized_url = normalize_url(url)

    url_id = insert_url(cursor, normalized_url)

    if url_id is None:
        existing_url_data = is_url_added(cursor, normalized_url)
        flash('Страница уже существует', 'info')
        return redirect(
            url_for('show_url', url_id=existing_url_data)
        )

    conn.commit()
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('show_url', url_id=url_id))


@app.route('/urls/<int:url_id>/checks', methods=['POST'])
@init_cursor
def create_check(cursor, conn, url_id):
    url_data = get_url_name(cursor, url_id)

    if url_data is None:
        flash('URL не найден.', 'danger')
        return redirect(url_for('list_urls'))

    url_name = url_data[0]

    response = fetch_url(url_name)
    status_code = response.status_code

    h1_content, title_content, description_content = parse_html(
        response.text
    )

    created_at = date.today()

    insert_check(
        cursor,
        url_id,
        status_code,
        h1_content,
        title_content,
        description_content,
        created_at
    )
    conn.commit()

    flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_url', url_id=url_id))


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
