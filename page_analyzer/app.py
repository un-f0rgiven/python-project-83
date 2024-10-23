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
import requests
from dotenv import load_dotenv
from datetime import date
from bs4 import BeautifulSoup
from page_analyzer.check_urls import is_valid_url, normalize_url
from page_analyzer.requests import fetch_url
from page_analyzer.sql_queries import (fetch_url_data,
                                       get_urls,
                                       insert_url,
                                       exist_url,
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


@app.route('/', methods=['GET'])
def get_index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def post_index():
    return ('Метод не разрешен', 405)


@app.route('/urls/<int:url_id>')
def show_url(url_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            url_data, checks = fetch_url_data(cursor, url_id)

            flashed_messages = get_flashed_messages(with_categories=True)

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
def handle_get_request():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            urls = get_urls(cursor)
            return render_template('list_urls.html', urls=urls)


@app.post('/urls')
def handle_post_request():
    url = request.form.get('url')

    if not is_valid_url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html', url=url), 422

    normalized_url = normalize_url(url)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                url_id = insert_url(cursor, normalized_url)

                if url_id is None:
                    existing_url_data = exist_url(cursor, normalized_url)
                    flash('Страница уже существует', 'info')
                    return redirect(
                        url_for('show_url', url_id=existing_url_data[0])
                    )

                conn.commit()
                flash('Страница успешно добавлена', 'success')
                return redirect(url_for('show_url', url_id=url_id))

    except Exception:
        flash('Ошибка добавления URL. Попробуйте снова.', 'danger')
        return render_template('index.html', url=url), 422

    return render_template('index.html', url=url), 422


@app.route('/urls/<int:url_id>/checks', methods=['POST'])
def create_check(url_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
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

    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', 'danger')
    except Exception:
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', url_id=url_id))


def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    h1_content = soup.find('h1').get_text() if soup.find('h1') else ''
    title_content = soup.title.string if soup.title else ''
    description_content = soup.find('meta', attrs={'name': 'description'})
    description_content = (
        description_content['content'] if description_content else ''
    )

    return h1_content, title_content, description_content
