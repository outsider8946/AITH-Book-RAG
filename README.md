# AITH Book RAG

## Usage

To split the text into chapters only, run the following command:

```bash
python utils/text_splitter.py
```

## Entities and relations

- Generate with LLM and save to `data/entities_and_relations`:

```bash
poetry run python utils/db_loader.py
```

- Download pre-generated JSONs from the shared Drive folder into `data/entities_and_relations`:

```bash
poetry run python utils/download_entities.py
```

## Development

To install the project dependencies:

```bash
poetry install
```

To install pre-commit hooks:

```bash
pre-commit install
```

## Run locally (dev)

- Backend (FastAPI):
  ```bash
  poetry install
  poetry run uvicorn backend.main:app --reload --port 8000
  ```
- Frontend (Vite):
  ```bash
  cd frontend
  pnpm install
  pnpm dev
  ```

## Run with Docker

You can run the entire application (Frontend + Backend) using Docker Compose.

```bash
docker-compose up --build
```

- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

The setup includes hot-reloading for both frontend and backend.

