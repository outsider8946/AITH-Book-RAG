import os
from pathlib import Path

import gdown
from dotenv import load_dotenv


ENV_DRIVE_NAME = "DRIVE_FOLDER_URL"
TARGET_DIR = Path("./data/entities_and_relations")


def main() -> None:
    """
    Download all JSONs from the shared Google Drive folder into TARGET_DIR.
    The folder URL can be overridden via the DRIVE_FOLDER_URL env var (e.g., in .env).
    """

    load_dotenv()
    folder_url = os.getenv(ENV_DRIVE_NAME)
    if not folder_url:
        raise ValueError(
            f"Folder URL is not set. Provide {ENV_DRIVE_NAME} in environment or .env."
        )

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    gdown.download_folder(
        url=folder_url,
        output=str(TARGET_DIR),
        remaining_ok=True,
        quiet=False,
        resume=True,
    )


if __name__ == "__main__":
    main()
