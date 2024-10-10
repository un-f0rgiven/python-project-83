from flask import Flask, render_template, redirect, url_for, request, flash
import os
import psycopg2
import logging
import re
import validators
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
app.secret_key = os.getenv('SECRET_KEY')  # Убедитесь, что вы добавили секретный ключ в .env

# Подключение к базе данных
def get_db_connection():
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        raise

# Нормализация URL
def normalize_url(url):
    parsed_url = urlparse(url)  # Разобрать URL
    # Убираем лишние пробелы и приводим домен к нижнему регистру
    netloc = parsed_url.netloc.strip().lower()
    # Формируем нормализованный URL
    normalized_url = urlunparse((parsed_url.scheme, netloc, parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))
    return normalized_url

# Валидация URL
def is_valid_url(url):
    # Проверка на длину
    if len(url) > 255:
        return False
    return validators.url(url)

# Обработчик для добавления URL
@app.route('/', methods=['GET', 'POST'])
def home():
    error_message = None  # Переменная для хранения сообщения об ошибке
    if request.method == 'POST':
        url = request.form.get('url')
        if is_valid_url(url):
            normalized_url = normalize_url(url)  # Нормализуем URL
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        # Проверка наличия нормализованного URL в базе данных
                        cursor.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
                        existing_url = cursor.fetchone()

                        if existing_url:
                            flash('Этот URL уже существует!', 'info')  # Сообщение о существующем URL
                            return redirect(url_for('show_url', url_id=existing_url[0]))  # Перенаправление на существующий URL

                        # Добавление нового нормализованного URL
                        cursor.execute("INSERT INTO urls (name) VALUES (%s) RETURNING id", (normalized_url,))
                        url_id = cursor.fetchone()[0]
                conn.commit()
                flash('URL успешно добавлен!', 'success')  # Сообщение об успешном добавлении
                return redirect(url_for('show_url', url_id=url_id))  # Перенаправляем на страницу нового URL
            except psycopg2.IntegrityError:
                flash('Этот URL уже существует в базе данных!', 'warning')  # Сообщение о дубликате
            except Exception as e:
                flash('Ошибка добавления URL. Попробуйте снова.', 'danger')  # Ошибка добавления URL
        else:
            flash('Некорректный URL. Пожалуйста, введите действительный адрес URL.', 'danger')  # Ошибка валидации URL

    # Возвращаем шаблон для GET-запроса или в случае ошибки
    return render_template('index.html', error_message=error_message)


@app.route('/urls/<int:url_id>')
def show_url(url_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Извлекаем URL по ID
                cursor.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
                url_data = cursor.fetchone()

                if url_data is None:
                    flash('URL не найден.', 'danger')  # Если URL не найден
                    return redirect(url_for('home'))  # Перенаправление на главную страницу

                return render_template('show_url.html', url_id=url_data[0], url_name=url_data[1], created_at=url_data[2])  # Передаем найденные данные в шаблон
    except Exception as e:
        logging.exception("Ошибка при получении URL.")
        flash('Ошибка при получении URL. Попробуйте снова.', 'danger')
        return redirect(url_for('home'))


@app.route('/urls')
def list_urls():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Извлекаем все URL, сортируя по дате создания (новые записи первыми)
                cursor.execute("SELECT id, name FROM urls ORDER BY created_at DESC")
                urls = cursor.fetchall()  # Получаем все записи

                return render_template('list_urls.html', urls=urls)  # Передаем записи в шаблон
    except Exception as e:
        logging.exception("Ошибка при получении списка URL.")
        flash('Ошибка при получении списка URL. Попробуйте снова.', 'danger')
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)