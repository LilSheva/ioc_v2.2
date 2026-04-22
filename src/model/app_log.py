"""Единая точка доставки служебных сообщений в GUI-консоль main-tab'а.

Безопасен для безконсольной .exe-сборки: никогда не пишет в stdout.
До регистрации UI-sink'а сообщения копятся в буфер, при `attach_ui()`
буфер выливается в консоль и все последующие вызовы идут туда напрямую.
"""

from typing import Callable, List, Optional


_SINK: Optional[Callable[[str], None]] = None
_BUFFER: List[str] = []


def attach_ui(sink: Callable[[str], None]) -> None:
    """Регистрирует функцию вывода (обычно `MainTab.log`) и сбрасывает буфер."""
    global _SINK
    _SINK = sink
    pending, _BUFFER[:] = list(_BUFFER), []
    for msg in pending:
        try:
            _SINK(msg)
        except Exception:
            pass


def log(msg: str) -> None:
    """Отправляет сообщение в GUI-консоль или копит в буфер до её готовности."""
    if _SINK is None:
        _BUFFER.append(msg)
        return
    try:
        _SINK(msg)
    except Exception:
        pass
