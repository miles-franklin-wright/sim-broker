FROM python:3.12-slim
WORKDIR /app
COPY ../pyproject.toml ../poetry.lock ./
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev
COPY .. .
CMD ["poetry", "run", "python", "loader/load_parquet.py"]
