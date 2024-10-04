from flask import Flask, render_template, redirect, url_for, request, flash
import os
import psycopg2
import logging
import re
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

# Валидация URL
def is_valid_url(url):
    # Проверка на длину
    if len(url) > 255:
        return False
    # Регулярное выражение для проверки формата URL
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # Протокол
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # Домен
        r'localhost|'  # Локальный адрес
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6
        r'(?::\d+)?'  # Порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # Оставшаяся часть URL
    return re.match(regex, url) is not None

# Обработчик для добавления URL
@app.route('/', methods=['GET', 'POST'])
def home():
    error_message = None  # Переменная для хранения сообщения об ошибке
    if request.method == 'POST':
        url = request.form['url']
        if is_valid_url(url):
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        # Проверка наличия URL в базе данных
                        cursor.execute("SELECT id FROM urls WHERE name = %s", (url,))
                        existing_url = cursor.fetchone()

                        if existing_url:
                            flash('Этот URL уже существует!', 'info')  # Сообщение о существующем URL
                            return redirect(url_for('show_url', url_id=existing_url[0]))  # Перенаправление на существующий URL

                        # Добавление нового URL
                        cursor.execute("INSERT INTO urls (name) VALUES (%s) RETURNING id", (url,))
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
                cursor.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
                url = cursor.fetchone()
                if url:
                    return render_template('show_url.html', url=url[0], data_test_url="url")  # Передаем data-test атрибут
                else:
                    return "URL не найден", 404
    except Exception as e:
        logging.error(f"Error retrieving URL: {e}")
        return "Ошибка при получении URL", 500

@app.route('/urls')
def list_urls():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Запрос всех URL, отсортированных по времени добавления (предполагается, что есть столбец `created_at`)
                cursor.execute("SELECT id, name FROM urls ORDER BY id DESC")  # ID должно быть последовательно увеличиваться
                urls = cursor.fetchall()  # Получаем все записи
            return render_template('list_urls.html', urls=urls, data_test_urls="urls")  # Передаем атрибут data-test
    except Exception as e:
        logging.error(f"Error retrieving URLs: {e}")
        return "Ошибка при получении URL", 500

if __name__ == '__main__':
    app.run(debug=True)