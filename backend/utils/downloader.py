import os
import asyncio
from pathlib import Path
import gdown
import httpx
import logging
from backend.utils.config_loader import config


class Downloader:
    logger = logging.getLogger(__name__)
    ollama_url = os.environ.get("OLLAMA_URL", "http://ollama:11434")
    embedding_model = config.embeddings.ollama_model_name
    path2data = Path("./backend/data")
    data = [
        ("🗂️ RAW text", os.environ.get("RAW_TEXT_LINK", ""), "monte-cristo.txt"),
        ("📄 nodes.json", os.environ.get("NODES_LINK", ""), "nodes.json"),
        ("📄 edges.json", os.environ.get("EDGES_LINK", ""), "edges.json"),
        ("📄 names_map.json", os.environ.get("NAMES_MAP_LINK", ""), "names_map.json"),
    ]

    async def download_ollama_model(self):
        """Гарантирует, что Ollama запущен и модель загружена."""
        self.logger.info(f"Начало скачивание модели Ollama: {self.embedding_model}")
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            self.logger.info("⏳ Ожидание доступности Ollama API...")
            for _ in range(30):  # макс. 30 сек
                try:
                    resp = await client.get(f"{self.ollama_url}/")
                    if resp.status_code in (
                        200,
                        404,
                    ):  # 404 — нормально (корень не реализован)
                        self.logger.info("✅ Ollama API доступен.")
                        break
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                await asyncio.sleep(1)
            else:
                raise RuntimeError("Ollama API не стал доступен за 30 секунд")

            self.logger.info(f"📥 Проверка наличия модели '{self.embedding_model}'...")
            try:
                resp = await client.get(f"{self.ollama_url}/api/tags")
                resp.raise_for_status()
                models = {m["name"] for m in resp.json().get("models", [])}
                full_name = f"{self.embedding_model}:latest"

                if full_name in models or self.embedding_model in models:
                    self.logger.info(
                        "✅ Модель '%s' уже загружена.", self.embedding_model
                    )
                    return
            except Exception as e:
                self.logger.warning(f"Не удалось получить список моделей: {e}")

            self.logger.info(
                f"🔽 Загружаем модель '{self.embedding_model}' в Ollama..."
            )
            try:
                response = await client.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": self.embedding_model, "stream": False},
                    timeout=30,
                )
                response.raise_for_status()
                self.logger.info(
                    f"✅ Модель '{self.embedding_model}' успешно загружена."
                )
            except Exception as e:
                raise RuntimeError(
                    f"Не удалось загрузить модель '{self.embedding_model}': {e}"
                )

    def download_data(self) -> None:
        """Скачивание данных для графа знаний"""
        self.logger.info("Начало скачивание данных!")
        self.path2data.mkdir(exist_ok=True)

        for description, url, filename in self.data:
            destination = self.path2data / filename
            self.logger.info(description)

            if destination.exists():
                self.logger.info(f"✅ Файл {filename} уже существует")
                continue

            try:
                gdown.download(url, str(destination), fuzzy=True, quiet=False)
                self.logger.info(f"✅ Скачан: {filename}")
            except Exception as e:
                raise RuntimeError(f"❌ Ошибка при скачивании {filename}: {e}")

        self.logger.info("✅ Скачивание завершено!")

    async def download(self) -> None:
        await self.download_ollama_model()
        self.download_data()
