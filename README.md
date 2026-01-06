# AITH Book RAG

## Preinstall
- Poetry
- Docker
- Python

## SetUp
Clone reposiory with following command:

```bash
git clone https://github.com/outsider8946/AITH-Book-RAG.git
```
and go to root of project:

```bash
cd AITH-Book-RAG/
```

Install the project dependencies:

```bash
poetry install
```
```bash
poetry env activate
```
and copy poetry env to cmd (for example):
```bash
source /home/dolor/.cache/pypoetry/virtualenvs/aith-book-rag-QRipLkJA-py3.11/bin/activate
```
Copy enviroment variables example with command:
```bash
cp .env.example .env
```
and set enviroment variables (you can use Mistral or DeepSeek)

Run docker:
You can run the entire application (Frontend + Backend) using Docker Compose.

```bash
docker-compose up --build
```


- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

The setup includes hot-reloading for both frontend and backend.



