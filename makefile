install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

sql:
	poetry run python page_analyzer/make_sql.py

lint:
	poetry run flake8

PORT ?= 8000

start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

.PHONY: install lint

build:
	./build.sh