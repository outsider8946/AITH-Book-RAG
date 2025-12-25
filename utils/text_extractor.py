import re
import os
from typing import List, Dict


class TextExtractor:
    def __init__(self):
        self.path2save = "./data/structed_text"
        self.chapter_pattern = r"^([IVXLCDM]+)\.\s+(.+)$"  # pattern for chapters
        self.part_pattern = r"^Часть\s+(первая|вторая|третья|четвертая|пятая|шестая)"  # pattern for parts

    def extract_chapters(self, file_path: str) -> List[Dict[str, str]]:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        except UnicodeDecodeError:
            for encoding in ["cp1251", "iso-8859-1", "maccyrillic"]:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        content = file.read()
                    break
                except UnicodeDecodeError:
                    continue

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

            part_match = re.match(self.part_pattern, line, re.IGNORECASE)
            if part_match:
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

            chapter_match = re.match(self.chapter_pattern, line)
            if chapter_match:
                if current_chapter and current_content:
                    chapters.append(
                        self._create_chapter_dict(
                            current_chapter, current_content, current_part
                        )
                    )

                roman_num = chapter_match.group(1)
                title = chapter_match.group(2)
                current_chapter = {
                    "roman_number": roman_num,
                    "title": title,
                    "arabic_number": self.roman2arabic(roman_num),
                }
                current_content = []
                in_chapter = True
                continue

            if in_chapter and current_chapter:
                if any(marker in line for marker in ["notes", "Примечания"]):
                    break
                current_content.append(line)

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

    def roman2arabic(self, roman: str) -> int:
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

    def save_chapters(self, chapters: List[Dict]):
        if not os.path.exists(self.path2save):
            os.makedirs(self.path2save)

        for chapter in chapters:
            part_dir = os.path.join(self.path2save, chapter["part"])
            if not os.path.exists(part_dir):
                os.makedirs(part_dir)

            filename = f"{chapter['arabic_number']:02d}_{chapter['title']}.txt"
            filename = re.sub(r'[<>:"/\\|?*]', "", filename)

            filepath = os.path.join(part_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Часть: {chapter['part']}\n")
                f.write(f"Глава: {chapter['full_title']}\n")
                f.write("=" * 50 + "\n\n")
                f.write(chapter["content"])

    def extract(self, file_path: str, save_to_files: bool = True):
        print("Extracting RAW text...")
        chapters = self.extract_chapters(file_path)

        if not chapters:
            print("Chapters not fond. Check structure")
            return []

        if save_to_files:
            self.save_chapters(chapters)

        return chapters


extractor = TextExtractor()
extractor.extract("./data/monte-cristo.txt")
