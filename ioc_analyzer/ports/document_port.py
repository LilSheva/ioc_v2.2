"""
Порт для чтения документов Word.
"""

import abc
from dataclasses import dataclass



@dataclass
class ParagraphData:
    """
    Данные отдельного абзаца документа.
    """
    text: str
    has_border: bool
    xml_str: str = ""


class DocumentPort(abc.ABC):
    """
    Интерфейс для извлечения содержимого документов.
    """

    @abc.abstractmethod
    def read_paragraphs(self, file_path: str) -> list[ParagraphData]:
        """
        Считывает абзацы документа с метаданными разметки.

        Args:
            file_path: Путь к файлу документа .docx.

        Returns:
            Список абзацев с указанием наличия горизонтальных границ.
        """
        pass

    @abc.abstractmethod
    def read_full_text(self, file_path: str) -> str:
        """
        Считывает весь текст из документа (включая таблицы).

        Args:
            file_path: Путь к файлу документа .docx.

        Returns:
            Полный текст документа.
        """
        pass
