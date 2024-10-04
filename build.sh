#!/usr/bin/env bash

# Проверка наличия переменной окружения DATABASE_URL
if [[ -z "$DATABASE_URL" ]]; then
    echo "Ошибка: Переменная окружения DATABASE_URL не задана!"
    exit 1
fi

make install

# Загрузка SQL-файла в подключенную базу данных
psql -a -d "$DATABASE_URL" -f database.sql