"""
Вкладка "Инструкция" — загружает и отображает instruction.md с форматированием.
"""

import os
import re
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ...utils import get_application_base_path


class InfoTab:
    """Вкладка с инструкцией — рендерит markdown из instruction.md."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        self._setup_ui()
        self._configure_tags()
        self._load_instruction()

    def _setup_ui(self):
        """Создание интерфейса: Text (scrollable) + easter egg."""
        # Scrollable text area
        text_frame = ttk.Frame(self.frame)
        text_frame.pack(fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.text = tk.Text(
            text_frame,
            wrap="word",
            relief="flat",
            padx=20,
            pady=15,
            cursor="arrow",
            state="disabled",
            highlightthickness=0,
            borderwidth=0,
            spacing1=1,
            spacing3=1,
        )
        self.text.pack(fill=BOTH, expand=True)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.text.yview)

        # Easter egg at the bottom
        ttk.Separator(self.frame, orient=HORIZONTAL).pack(fill=X, pady=(10, 5))
        ttk.Label(
            self.frame,
            text='"РАБОТАЕТ — НЕ ТРОГАЙ"  (c) Отдел ИБ',
            font=("TkDefaultFont", 9),
            bootstyle=SECONDARY,
        ).pack(pady=(0, 5))

    def _configure_tags(self):
        """Определение текстовых тегов для форматирования."""
        default_font = "Segoe UI"
        mono_font = "Consolas"

        self.text.tag_configure("h2", font=(default_font, 16, "bold"),
                                spacing1=14, spacing3=6)
        self.text.tag_configure("h3", font=(default_font, 13, "bold"),
                                spacing1=10, spacing3=4)
        self.text.tag_configure("paragraph", font=(default_font, 10),
                                spacing1=2, spacing3=2, lmargin1=5, lmargin2=5)
        self.text.tag_configure("bold", font=(default_font, 10, "bold"))
        self.text.tag_configure("inline_code", font=(mono_font, 10),
                                background="#3a3a3a", foreground="#e0e0e0")
        self.text.tag_configure("bullet", font=(default_font, 10),
                                lmargin1=25, lmargin2=40,
                                spacing1=2, spacing3=2)
        self.text.tag_configure("numbered", font=(default_font, 10),
                                lmargin1=25, lmargin2=40,
                                spacing1=2, spacing3=2)
        self.text.tag_configure("code_block", font=(mono_font, 10),
                                background="#2d2d2d", foreground="#e0e0e0",
                                lmargin1=20, lmargin2=20, rmargin=20,
                                spacing1=2, spacing3=2)
        self.text.tag_configure("spacing", font=(default_font, 4),
                                spacing1=0, spacing3=0)

    def _load_instruction(self):
        """Загрузить instruction.md и отрендерить."""
        base = get_application_base_path()
        path = os.path.join(base, "instruction.md")

        if not os.path.isfile(path):
            self.text.configure(state="normal")
            self.text.insert("end", f"Файл instruction.md не найден.\n\n", "h3")
            self.text.insert("end", f"Ожидаемый путь:\n{path}", "paragraph")
            self.text.configure(state="disabled")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.text.configure(state="normal")
            self.text.insert("end", f"Ошибка чтения instruction.md:\n{e}", "paragraph")
            self.text.configure(state="disabled")
            return

        self._render_markdown(content)

    def _render_markdown(self, text):
        """Построчный парсер markdown → вставка в Text с тегами."""
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")

        lines = text.split("\n")
        in_code_block = False
        i = 0

        while i < len(lines):
            line = lines[i]

            # Code block toggle
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                if in_code_block:
                    # start of code block — skip the ``` line
                    i += 1
                    continue
                else:
                    # end of code block
                    i += 1
                    continue

            if in_code_block:
                self.text.insert("end", line + "\n", "code_block")
                i += 1
                continue

            stripped = line.strip()

            # Blank line → spacing
            if not stripped:
                self.text.insert("end", "\n", "spacing")
                i += 1
                continue

            # H2
            if stripped.startswith("## "):
                header_text = stripped[3:]
                self.text.insert("end", header_text + "\n", "h2")
                i += 1
                continue

            # H3
            if stripped.startswith("### "):
                header_text = stripped[4:]
                self.text.insert("end", header_text + "\n", "h3")
                i += 1
                continue

            # H1 (treat same as H2)
            if stripped.startswith("# "):
                header_text = stripped[2:]
                self.text.insert("end", header_text + "\n", "h2")
                i += 1
                continue

            # Bullet list
            bullet_match = re.match(r"^[-*]\s+(.*)", stripped)
            if bullet_match:
                self._insert_inline("  \u2022  " + bullet_match.group(1) + "\n", "bullet")
                i += 1
                continue

            # Numbered list
            num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
            if num_match:
                prefix = f"  {num_match.group(1)}.  "
                self._insert_inline(prefix + num_match.group(2) + "\n", "numbered")
                i += 1
                continue

            # Plain paragraph
            self._insert_inline(stripped + "\n", "paragraph")
            i += 1

        self.text.configure(state="disabled")

    def _insert_inline(self, text, base_tag):
        """Вставка текста с обработкой **bold** и `code` inline."""
        # Pattern: **bold** or `code`
        pattern = re.compile(r"(\*\*(.+?)\*\*|`([^`]+?)`)")
        last_end = 0

        for match in pattern.finditer(text):
            # Insert text before match
            before = text[last_end:match.start()]
            if before:
                self.text.insert("end", before, base_tag)

            if match.group(2) is not None:
                # **bold**
                self.text.insert("end", match.group(2), (base_tag, "bold"))
            elif match.group(3) is not None:
                # `code`
                self.text.insert("end", match.group(3), (base_tag, "inline_code"))

            last_end = match.end()

        # Insert remaining text
        remaining = text[last_end:]
        if remaining:
            self.text.insert("end", remaining, base_tag)

    def get_frame(self):
        return self.frame
