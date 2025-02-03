# Используем официальный образ Python
FROM python:3.12

# Устанавливаем рабочую директорию в контейнере, аналогичную проекту на локальном
WORKDIR /domainname

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем код проекта внутрь контейнера
COPY . .


RUN chmod a+x /domainname/app.sh