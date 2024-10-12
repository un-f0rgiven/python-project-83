from flask import Flask, render_template, redirect, url_for, request, flash, get_flashed_messages  # Импортируем необходимые модули из Flask
import os  # Для работы с операционной системой
import psycopg2  # Для подключения к PostgreSQL
import logging  # Для логирования
import re  # Для работы с регулярными выражениями
import validators  # Для валидации URL
import requests  # Для выполнения HTTP-запросов
from urllib.parse import urlparse, urlunparse  # Для разбора и сборки URL
from dotenv import load_dotenv  # Для загрузки переменных окружения из файла .env
from datetime import date  # Для работы с датами
from bs4 import BeautifulSoup # Для парсинга HTML

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)  # Устанавливаем уровень логирования на INFO

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
    logging.info("Разбираем URL на компоненты. Результат: %s", parsed_url)
    # Убираем лишние пробелы и приводим домен к нижнему регистру
    netloc = parsed_url.netloc.strip().lower()  
    # Формируем нормализованный URL из разобранных компонентов
    normalized_url = urlunparse((parsed_url.scheme, netloc, "", "", "", ""))
    logging.info("Normalize_url: %s", normalized_url)
    if normalized_url.endswith('/'):
        normalized_url = normalized_url[:-1]
    return normalized_url  # Возвращаем нормализованный URL

# Функция для валидации URL
def is_valid_url(url):
    # Проверяем, не превышает ли длина URL 255 символов
    if len(url) > 255:
        return False
    return validators.url(url)  # Используем validators для проверки валидности URL

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Перенаправление на /urls для добавления нового URL
        return redirect(url_for('manage_urls'))  # Перенаправление на обработчик /urls

    # Возвращаем шаблон для GET-запроса
    return render_template('index.html')


@app.route('/urls/<int:url_id>')  # Обработчик для отображения конкретного URL
def show_url(url_id):
    try:
        # Устанавливаем соединение с базой данных
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Извлекаем URL по ID
                cursor.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
                url_data = cursor.fetchone()  # Получаем данные о URL

                flashed_messages = get_flashed_messages(with_categories=True)

                if url_data is None:  # Если URL не найден
                    flash('URL не найден.', 'danger')  # Сообщение об ошибке
                    return redirect(url_for('home'))  # Перенаправление на главную страницу
                
                # Извлекаем проверки для данного URL
                cursor.execute("SELECT id, status_code, h1, title, description, created_at FROM url_checks WHERE url_id = %s", (url_id,))
                checks = cursor.fetchall()  # Получаем все проверки

                # Передаем найденные данные и проверки в шаблон
                return render_template('show_url.html', url_id=url_data[0], url_name=url_data[1], created_at=url_data[2], checks=checks, flashed_messages=flashed_messages)  
    except Exception as e:
        logging.exception("Ошибка при получении URL.")  # Логируем исключение
        flash('Ошибка при получении URL. Попробуйте снова.', 'danger')  # Сообщение об ошибке
        return redirect(url_for('home'))  # Перенаправление на главную страницу

@app.route('/urls', methods=['GET', 'POST'])
def manage_urls():
    if request.method == 'POST':
        # Обработка POST-запроса для добавления нового URL
        url = request.form.get('url')
        logging.info("Пользователь ввёл URL: %s", url)
        
        if is_valid_url(url):  # Проверка валидности URL
            normalized_url = normalize_url(url)
            logging.info('Normalize URL: %s', normalized_url)
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("INSERT INTO urls (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id", (normalized_url,))
                        url_id = cursor.fetchone()[0] if cursor.rowcount > 0 else None
                        logging.info('Запрос выполнен: INSERT INTO urls (name) VALUES (%s); Результат: %s', normalized_url, url_id)
                        conn.commit()
                        if url_id is None:
                            cursor.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
                            existing_url = cursor.fetchone()
                            if existing_url:
                                flash('Страница уже существует', 'info')
                                return redirect(url_for('show_url', url_id=existing_url[0]))
                        else:
                            flash('Страница успешно добавлена', 'success')
                            return redirect(url_for('show_url', url_id=url_id))
            except psycopg2.IntegrityError:
                flash('Страница уже существует', 'warning')
            except Exception as e:
                flash('Ошибка добавления URL. Попробуйте снова.', 'danger')
        else:
            flash('Некорректный URL', 'danger')

        return redirect(url_for('home', url=url))  # Перенаправляем на главную страницу

    # Обработка GET-запроса для отображения списка URL
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(""" 
                    SELECT u.id, u.name, uc.status_code,
                           MAX(uc.created_at) AS last_check_date
                    FROM urls u
                    LEFT JOIN url_checks uc ON u.id = uc.url_id
                    GROUP BY u.id, u.name, uc.status_code
                    ORDER BY last_check_date DESC
                """)
                urls = cursor.fetchall()  # Получаем все записи

                return render_template('list_urls.html', urls=urls)  # Передаем записи в шаблон
    except Exception as e:
        logging.exception("Ошибка при получении списка URL.")
        flash('Ошибка при получении списка URL. Попробуйте снова.', 'danger')
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

        # Парсинг HTML-страницы
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение содержимого тегов
        h1_content = soup.find('h1').get_text() if soup.find('h1') else ''
        title_content = soup.title.string if soup.title else ''
        description_content = soup.find('meta', attrs={'name': 'description'})
        description_content = description_content['content'] if description_content else ''

        # Записываем код ответа и текущее время в базу данных
        created_at = date.today()  # Получаем текущее время для поля created_at
        with get_db_connection() as conn:  # Устанавливаем соединение с базой данных
            with conn.cursor() as cursor:  # Создаем курсор для выполнения запросов
                # Выполняем запрос для вставки данных о проверке в таблицу url_checks
                cursor.execute(
                    "INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (url_id, status_code, h1_content,title_content, description_content, created_at)
                )
                conn.commit()  # Сохраняем изменения в базе данных

        flash('Страница успешно проверена', 'success')  # Сообщение об успешном завершении проверки
    except requests.exceptions.RequestException as e:
        # Обработка ошибок, возникающих при выполнении запроса
        logging.exception("Ошибка при проверке URL.")  # Логируем исключение
        flash('Произошла ошибка при проверке', 'danger')  # Сообщение об ошибке
    except Exception as e:
        # Обработка других ошибок, например, ошибок базы данных
        logging.exception("Ошибка при записи в базу данных: %s", str(e))  # Логируем исключение
        flash('Произошла ошибка при проверке', 'danger')  # Сообщение об ошибке

    return redirect(url_for('show_url', url_id=url_id))  # Перенаправление на страницу URL после завершения


if __name__ == '__main__':
    app.run(debug=True)