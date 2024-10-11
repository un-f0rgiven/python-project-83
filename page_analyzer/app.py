from flask import Flask, render_template, redirect, url_for, request, flash  # Импортируем необходимые модули из Flask
import os  # Для работы с операционной системой
import psycopg2  # Для подключения к PostgreSQL
import logging  # Для логирования
import re  # Для работы с регулярными выражениями
import validators  # Для валидации URL
import requests  # Для выполнения HTTP-запросов
from urllib.parse import urlparse, urlunparse  # Для разбора и сборки URL
from dotenv import load_dotenv  # Для загрузки переменных окружения из файла .env
from datetime import date  # Для работы с датами

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)  # Устанавливаем уровень логирования на INFO

# Создание экземпляра Flask приложения
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
app.secret_key = os.getenv('SECRET_KEY')  # Получаем секретный ключ из переменных окружения

# Функция для подключения к базе данных
def get_db_connection():
    try:
        database_url = os.getenv('DATABASE_URL')  # Получаем URL базы данных из переменных окружения
        conn = psycopg2.connect(database_url)  # Устанавливаем соединение с базой данных
        return conn  # Возвращаем объект соединения
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")  # Логируем ошибку подключения
        raise  # Поднимаем исключение

# Функция для нормализации URL
def normalize_url(url):
    parsed_url = urlparse(url)  # Разбираем URL на компоненты
    # Убираем лишние пробелы и приводим домен к нижнему регистру
    netloc = parsed_url.netloc.strip().lower()  
    # Формируем нормализованный URL из разобранных компонентов
    normalized_url = urlunparse((parsed_url.scheme, netloc, parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))
    return normalized_url  # Возвращаем нормализованный URL

# Функция для валидации URL
def is_valid_url(url):
    # Проверяем, не превышает ли длина URL 255 символов
    if len(url) > 255:
        return False
    return validators.url(url)  # Используем validators для проверки валидности URL

# Обработчик для главной страницы, добавления URL
@app.route('/', methods=['GET', 'POST'])
def home():
    error_message = None  # Переменная для хранения сообщения об ошибке
    if request.method == 'POST':  # Если метод запроса POST
        url = request.form.get('url')  # Получаем URL из формы
        if is_valid_url(url):  # Проверяем валидность URL
            normalized_url = normalize_url(url)  # Нормализуем URL
            try:
                # Устанавливаем соединение с базой данных
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        # Выполняем вставку URL в базу данных с обработкой дубликатов
                        cursor.execute("INSERT INTO urls (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id", (normalized_url,))
                        url_id = cursor.fetchone()[0] if cursor.rowcount > 0 else None  # Получаем ID вставленного URL
                conn.commit()  # Сохраняем изменения в базе данных
                if url_id:  # Если URL был успешно добавлен
                    flash('URL успешно добавлен!', 'success')  # Сообщение об успешном добавлении
                    return redirect(url_for('show_url', url_id=url_id))  # Перенаправляем на страницу нового URL
                else:
                    flash('Этот URL уже существует!', 'info')  # Сообщение о существующем URL
                    cursor.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))  # Извлекаем ID существующего URL
                    existing_url = cursor.fetchone()  # Получаем существующий URL
                    return redirect(url_for('show_url', url_id=existing_url[0]))  # Перенаправляем на его страницу
                
            except psycopg2.IntegrityError:
                flash('Этот URL уже существует в базе данных!', 'warning')  # Сообщение о дубликате
            except Exception as e:
                flash('Ошибка добавления URL. Попробуйте снова.', 'danger')  # Ошибка добавления URL
        else:
            flash('Некорректный URL. Пожалуйста, введите действительный адрес URL.', 'danger')  # Ошибка валидации URL

    # Возвращаем шаблон для GET-запроса или в случае ошибки
    return render_template('index.html', error_message=error_message)


@app.route('/urls/<int:url_id>')  # Обработчик для отображения конкретного URL
def show_url(url_id):
    try:
        # Устанавливаем соединение с базой данных
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Извлекаем URL по ID
                cursor.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
                url_data = cursor.fetchone()  # Получаем данные о URL

                if url_data is None:  # Если URL не найден
                    flash('URL не найден.', 'danger')  # Сообщение об ошибке
                    return redirect(url_for('home'))  # Перенаправление на главную страницу
                
                # Извлекаем проверки для данного URL
                cursor.execute("SELECT id, status_code, h1, title, description, created_at FROM url_checks WHERE url_id = %s", (url_id,))
                checks = cursor.fetchall()  # Получаем все проверки

                # Передаем найденные данные и проверки в шаблон
                return render_template('show_url.html', url_id=url_data[0], url_name=url_data[1], created_at=url_data[2], checks=checks)  
    except Exception as e:
        logging.exception("Ошибка при получении URL.")  # Логируем исключение
        flash('Ошибка при получении URL. Попробуйте снова.', 'danger')  # Сообщение об ошибке
        return redirect(url_for('home'))  # Перенаправление на главную страницу

@app.route('/urls')  # Обработчик для отображения списка всех URL
def list_urls():
    try:
        # Устанавливаем соединение с базой данных
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Извлекаем все URL, включая дату последней проверки
                cursor.execute(""" 
                    SELECT u.id, u.name, 
                           MAX(uc.created_at) AS last_check_date
                    FROM urls u
                    LEFT JOIN url_checks uc ON u.id = uc.url_id
                    GROUP BY u.id, u.name
                    ORDER BY u.created_at DESC
                """)
                urls = cursor.fetchall()  # Получаем все записи

                # Передаем записи в шаблон
                return render_template('list_urls.html', urls=urls)  
    except Exception as e:
        logging.exception("Ошибка при получении списка URL.")  # Логируем исключение
        flash('Ошибка при получении списка URL. Попробуйте снова.', 'danger')  # Сообщение об ошибке
        return redirect(url_for('home'))  # Перенаправление на главную страницу


@app.route('/urls/<int:url_id>/checks', methods=['POST'])  # Декоратор для маршрута, обрабатывающего POST-запросы
def create_check(url_id):
    # Проверка соединения с базой данных
    if not get_db_connection():
        flash('Не удалось подключиться к базе данных. Попробуйте позже.', 'danger')  # Сообщение об ошибке
        return redirect(url_for('list_urls'))  # Перенаправление на страницу списка URL
    
    try:
        # Получаем URL для проверки из базы данных
        with get_db_connection() as conn:  # Устанавливаем соединение с базой данных
            with conn.cursor() as cursor:  # Создаем курсор для выполнения запросов
                # Выполняем запрос для получения имени URL по его ID
                cursor.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
                url_data = cursor.fetchone()  # Извлекаем данные о URL

                # Проверяем, существует ли URL
                if url_data is None:
                    flash('URL не найден.', 'danger')  # Сообщение об ошибке, если URL не найден
                    return redirect(url_for('list_urls'))  # Перенаправление на страницу списка URL

                url_name = url_data[0]  # Извлекаем имя URL из результата запроса

        # Выполняем HTTP-запрос к сайту и получаем статус-код ответа
        response = requests.get(url_name)  # Отправляем GET-запрос
        response.raise_for_status()  # Проверяем наличие ошибок HTTP
        status_code = response.status_code  # Получаем статус-код ответа

        # Записываем код ответа и текущее время в базу данных
        created_at = date.today()  # Получаем текущее время для поля created_at
        with get_db_connection() as conn:  # Устанавливаем соединение с базой данных
            with conn.cursor() as cursor:  # Создаем курсор для выполнения запросов
                # Выполняем запрос для вставки данных о проверке в таблицу url_checks
                cursor.execute(
                    "INSERT INTO url_checks (url_id, status_code, created_at) VALUES (%s, %s, %s)",
                    (url_id, status_code, created_at)
                )
                conn.commit()  # Сохраняем изменения в базе данных

        flash('Проверка прошла успешно!', 'success')  # Сообщение об успешном завершении проверки
    except requests.exceptions.RequestException as e:
        # Обработка ошибок, возникающих при выполнении запроса
        logging.exception("Ошибка при проверке URL.")  # Логируем исключение
        flash('Произошла ошибка при проверке.', 'danger')  # Сообщение об ошибке
    except Exception as e:
        # Обработка других ошибок, например, ошибок базы данных
        logging.exception("Ошибка при записи в базу данных: %s", str(e))  # Логируем исключение
        flash('Произошла ошибка при проверке.', 'danger')  # Сообщение об ошибке

    return redirect(url_for('show_url', url_id=url_id))  # Перенаправление на страницу URL после завершения


if __name__ == '__main__':
    app.run(debug=True)