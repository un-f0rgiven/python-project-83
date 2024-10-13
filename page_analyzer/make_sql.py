import os
# Для работы с операционной системой
from dotenv import load_dotenv
# Для загрузки переменных окружения из файла .env
import psycopg2
# Для подключения и работы с базой данных PostgreSQL

# Загружаем переменные окружения из файла .env
load_dotenv()


# Функция для подключения к базе данных
def get_db_connection():
    # Определяем функцию для установки соединения с базой данных
    try:
        # Начинаем блок try для обработки возможных исключений
        database_url = os.getenv('DATABASE_URL')
        # Получите URL базы данных из переменных окружения
        conn = psycopg2.connect(database_url)
        # Устанавливаем соединение с базой данных, используя полученный URL
        return conn
    # Возвращаем объект соединения
    except Exception as e:
        # Обрабатываем исключение, если возникла ошибка при подключении
        print(f"Error connecting to the database: {e}")
        # Выводим сообщение об ошибке подключения с деталями исключения
        raise
        # Поднимаем исключение выше, чтобы его можно было обработать позже


# Функция для выполнения SQL-скрипта из файла
def execute_sql_file(filename):
    # Определяем функцию execute_sql_file, которая принимает имя файла SQL
    with open(filename, 'r') as file:
        # Открываем файл с именем filename в режиме чтения
        sql_script = file.read()
        # Читаем содержимое файла и сохраняем его в переменной sql_script

    # Подключаемся к базе данных и выполняем скрипт
    with get_db_connection() as conn:
        # Устанавливаем соединение с базой данных
        with conn.cursor() as cursor:
            # Создаем курсор для выполнения SQL-запросов
            cursor.execute(sql_script)
            # Выполняем SQL-скрипт, считанный из файла
            conn.commit()
            # Фиксируем изменения в базе данных


# Проверяем, что данный файл выполняется как основная программа
if __name__ == '__main__':
    # Если этот файл запущен как основной модуль
    execute_sql_file(
        '/mnt/c/Users/Александр/Projects/python-project-83/database.sql'
    )
    # Вызываем функцию execute_sql_file с указанием пути к SQL-файлу
