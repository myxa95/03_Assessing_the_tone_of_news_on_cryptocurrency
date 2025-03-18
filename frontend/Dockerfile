FROM python:3.11-slim-buster

WORKDIR /app
COPY frontend ./frontend
COPY pyproject.toml poetry.lock ./

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        cmake \
        build-essential \
        gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Установка Poetry и зависимостей
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

WORKDIR /app/frontend
EXPOSE 8501

ENTRYPOINT ["streamlit", "run"]
CMD ["main.py"]