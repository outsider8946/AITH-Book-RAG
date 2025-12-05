import re
import os
from typing import List, Dict


class MonteCristoChapterExtractor:
    def __init__(self):
        # Паттерн для глав: римская цифра + точка + название
        self.chapter_pattern = r"^([IVXLCDM]+)\.\s+(.+)$"
        # Паттерн для частей
        self.part_pattern = r"^Часть\s+(первая|вторая|третья|четвертая|пятая|шестая)"

    def extract_chapters(self, file_path: str) -> List[Dict[str, str]]:
        """
        Извлекает главы из файла с учетом структуры частей
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        except UnicodeDecodeError:
            # Пробуем другие кодировки
            for encoding in ["cp1251", "iso-8859-1", "maccyrillic"]:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        content = file.read()
                    break
                except UnicodeDecodeError:
                    continue

        # Разделяем на строки
        lines = content.split("\n")

        chapters = []
        current_part = None
        current_chapter = None
        current_content = []
        in_chapter = False

        for _, line in enumerate(lines):
            line = line.strip()
            if line == "\n":
                continue

            # Определяем часть
            part_match = re.match(self.part_pattern, line, re.IGNORECASE)
            if part_match:
                # Сохраняем предыдущую главу при смене части
                if current_chapter and current_content:
                    chapters.append(
                        self._create_chapter_dict(
                            current_chapter, current_content, current_part
                        )
                    )

                current_part = part_match.group(0)
                current_content = []
                current_chapter = None
                in_chapter = False
                continue

            # Определяем начало главы
            chapter_match = re.match(self.chapter_pattern, line)
            if chapter_match:
                # Сохраняем предыдущую главу
                if current_chapter and current_content:
                    chapters.append(
                        self._create_chapter_dict(
                            current_chapter, current_content, current_part
                        )
                    )

                # Начинаем новую главу
                roman_num = chapter_match.group(1)
                title = chapter_match.group(2)
                current_chapter = {
                    "roman_number": roman_num,
                    "title": title,
                    "arabic_number": self.roman_to_arabic(roman_num),
                }
                current_content = []
                in_chapter = True
                continue

            # Если мы внутри главы, добавляем контент
            if in_chapter and current_chapter:
                # Пропускаем технические разделы в конце
                if any(marker in line for marker in ["notes", "Примечания"]):
                    break
                current_content.append(line)

        # Добавляем последнюю главу
        if current_chapter and current_content:
            chapters.append(
                self._create_chapter_dict(
                    current_chapter, current_content, current_part
                )
            )

        return chapters

    def _create_chapter_dict(
        self, chapter_info: Dict, content: List[str], part: str
    ) -> Dict[str, str]:
        """Создает словарь с информацией о главе"""
        full_content = "\n".join(content).strip()

        return {
            "part": part,
            "roman_number": chapter_info["roman_number"],
            "arabic_number": chapter_info["arabic_number"],
            "title": chapter_info["title"],
            "full_title": f"{chapter_info['roman_number']}. {chapter_info['title']}",
            "content": full_content,
            "content_length": len(full_content),
        }

    def roman_to_arabic(self, roman: str) -> int:
        """Конвертирует римские цифры в арабские"""
        roman_numerals = {
            "I": 1,
            "V": 5,
            "X": 10,
            "L": 50,
            "C": 100,
            "D": 500,
            "M": 1000,
        }

        result = 0
        prev_value = 0

        for char in reversed(roman.upper()):
            value = roman_numerals.get(char, 0)
            if value < prev_value:
                result -= value
            else:
                result += value
            prev_value = value

        return result

    def save_chapters(
        self, chapters: List[Dict], output_dir: str = "./data/monte_cristo_chapters"
    ):
        """Сохраняет главы в отдельные файлы с группировкой по частям"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for chapter in chapters:
            # Создаем папку для части, если ее нет
            part_dir = os.path.join(output_dir, chapter["part"])
            if not os.path.exists(part_dir):
                os.makedirs(part_dir)

            # Создаем безопасное имя файла
            filename = f"{chapter['arabic_number']:02d}_{chapter['title']}.txt"
            filename = re.sub(r'[<>:"/\\|?*]', "", filename)

            filepath = os.path.join(part_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Часть: {chapter['part']}\n")
                f.write(f"Глава: {chapter['full_title']}\n")
                f.write("=" * 50 + "\n\n")
                f.write(chapter["content"])

        print(f"Сохранено {len(chapters)} глав в папку '{output_dir}'")

    def analyze_structure(self, chapters: List[Dict]):
        """Анализирует структуру извлеченных глав"""
        parts = {}
        for chapter in chapters:
            part = chapter["part"]
            if part not in parts:
                parts[part] = []
            parts[part].append(chapter)

        print("Структура романа:")
        print("=" * 40)
        for part, part_chapters in parts.items():
            print(f"\n{part}: {len(part_chapters)} глав")
            for chap in part_chapters[:3]:  # Показываем первые 3 главы каждой части
                print(f"  - {chap['full_title']} ({chap['content_length']} символов)")


# Функция для быстрого использования
def process_monte_cristo(file_path: str, save_to_files: bool = True):
    """
    Основная функция для обработки файла с 'Графом Монте-Кристо'
    """
    extractor = MonteCristoChapterExtractor()

    print("Извлечение глав из файла...")
    chapters = extractor.extract_chapters(file_path)

    if not chapters:
        print("Главы не найдены. Проверьте формат файла.")
        return []

    print(f"Успешно извлечено глав: {len(chapters)}")

    # Анализ структуры
    extractor.analyze_structure(chapters)

    # Сохранение в файлы
    if save_to_files:
        extractor.save_chapters(chapters)

    # Показываем пример первой главы
    if chapters:
        first_chapter = chapters[0]
        print("\nПример первой главы:")
        print(f"Название: {first_chapter['full_title']}")
        print(f"Часть: {first_chapter['part']}")
        print(f"Длина: {first_chapter['content_length']} символов")
        print(f"Начало текста: {first_chapter['content'][:200]}...")

    return chapters


# Пример использования
if __name__ == "__main__":
    process_monte_cristo("full_text/avidreaders.ru__graf-monte-kristo.txt")
