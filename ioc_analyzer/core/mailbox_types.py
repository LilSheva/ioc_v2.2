"""Типы данных для серверной выкладки на шару."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MailboxLayout:
    """Пути подпапок на сетевой шаре для одного письма."""

    root: str
    task: str
    report: str
    templates: str
