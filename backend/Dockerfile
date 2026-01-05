FROM python:3.11-slim

WORKDIR /app

# Copy from project root (context is project root)
COPY pyproject.toml poetry.lock ./

# Install poetry
RUN pip install poetry

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy backend code
COPY backend/ ./

# Create __init__.py files
RUN touch __init__.py && \
    mkdir -p utils && \
    touch utils/__init__.py

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "n"]