### Hexlet tests and linter status:
[![Actions Status](https://github.com/un-f0rgiven/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/un-f0rgiven/python-project-83/actions)
[![Maintainability](https://codeclimate.com/github/un-f0rgiven/python-project-83/badges/gpa.svg)](https://codeclimate.com/github/un-f0rgiven/python-project-83/maintainability)

## - Учебный проект "Анализатор страниц"
Веб-сайт для быстрой и простой проверки сайтов на SEO-пригодность.
Вводите URL в форму и проверяйте сайты по заголовкам и описанию.

### - Требования
OS Linux
Python 3.9>
Poetry 1.8>
PostgreSQL 14>

### - Переменные окружения
В проекте используются следующие переменные окружения:  
**- SECRET_KEY** - уникальный секретный ключ, используемый для криптографических операций, таких как шифрование данных и создание токенов.  
**- Важно**: Необходимо использовать длинную и случайную строку для обеспечения безопасности вашего приложения. Не делитесь этим ключом публично!  
**- Генерация**: для генерации переменной вы можете использовать следующий код, который создаст случайный 64-символьный шестнадцатеричный ключ.  
    ```python
    import secrets
    
    secret_key = secrets.token_hex(32)
    print(secret_key)
**- Пример использования**: SECRET_KEY='ваш_сгенерированный_секретный_ключ'  

**- DATABASE_URL** - URL для подключения к базе данных. Содержит информацию о типе базы данных, имени пользователя, пароле, хосте и имени базы данных.  
**- Формат**: dialect://username:password@host:port/database  
    ```*dialect*: тип базы данных<br>
    *username*: имя пользователя для подключения к базе данных<br>
    *password*: пароль для доступа к базе данных<br>
    *host*: адрес сервера базы данных<br>
    *port*: порт для подключения к базе данных (по умолчанию для PostgreSQL - 5432)<br>
    *database*: имя базы данных, к которой нужно подключиться```  
**- Пример использования**: DATABASE_URL='postgresql://user:password@localhost:5432/mydatabase'

### - Установка
1. Установка производится через команду **make install**
2. Создание базы данных производится через команду **make sql**
3. Запуск производится через команду **make dev**
4. Развёртывание производится с использованием gunicorn через команду **make start**
5. Порт для запуска можно изменить через установку переменной окружения PORT **export PORT=<укажите_значение_порта>**

### - Демонстрация развёрнутого приложения:
https://python-project-83-kvtr.onrender.com/