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
