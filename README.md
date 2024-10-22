### Hexlet tests and linter status:
[![Actions Status](https://github.com/un-f0rgiven/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/un-f0rgiven/python-project-83/actions)
[![Maintainability](https://codeclimate.com/github/un-f0rgiven/python-project-83/badges/gpa.svg)](https://codeclimate.com/github/un-f0rgiven/python-project-83/maintainability)

**Учебный проект - Анализатор страниц**
Веб-сайт для быстрой и простой проверки сайтов на SEO-пригодность.
Вводите URL в форму и проверяйте сайты по заголовкам и описанию.

**Требования**
OS Linux
Python 3.9>
Poetry 1.8>
PostgreSQL 14>

**Установка**
Установка производится через команду:
*make install*
Создание базы данных производится через команду:
*make sql*
Запуск производится через команду:
*make dev*
Развёртывание производится с использованием gunicorn через команду:
*make start*
Порт для запуска можно изменить через установку переменной окружения PORT:
*export PORT=<укажите_значение_порта>*

### Демонстрация развёрнутого приложения:
https://python-project-83-kvtr.onrender.com/