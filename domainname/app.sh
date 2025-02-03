#!/bin/bash

# Проверка на существование файла wait-for-it.sh
if [ ! -f /usr/local/bin/wait-for-it ]; then
    echo "wait-for-it не найден, скачиваю..."
    curl -sSL https://github.com/vishnubob/wait-for-it/raw/master/wait-for-it.sh -o /usr/local/bin/wait-for-it
    chmod +x /usr/local/bin/wait-for-it
else
    echo "wait-for-it уже установлен."
fi

# Ждем, пока база данных будет доступна
echo "Waiting for database to be ready..."
wait-for-it container_db:5432 --timeout=33 -- python manage.py migrate

if [ $? -ne 0 ]; then
    echo "Django migrations failed"
    exit 1
fi

echo "Migrations complete"

# Выполняем collectstatic для сбора статики
echo "Running collectstatic..."
python manage.py collectstatic --noinput

sleep 15

# Запускаем gunicorn с более менее подробными логами
gunicorn app_domainname.wsgi:application --workers 4 --bind=0.0.0.0:8000 --log-level=debug --access-logfile - --error-logfile - --forwarded-allow-ips="*"