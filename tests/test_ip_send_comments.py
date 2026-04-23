"""Тесты построения per-IP комментариев для отправки на API.

Покрывают `AppController._build_ip_comments` и интеграцию с моком `send_to_api`,
проверяют что:
- ФСТЭК — общий bulletin для всех IP;
- ГосСОПКА — у каждого IP коммент собран из его собственного filename;
- дубликат IP из разных файлов → коммент берётся из первого встреченного;
- если filename не парсится по шаблону ГосСОПКА — fallback на имя без расширения;
- payload в send_to_api содержит правильную пару ip↔comment.

Запуск: python tests/test_ip_send_comments.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.controller.app_controller import AppController  # type: ignore
from src.model import api_sender as api_sender_module  # type: ignore


_failures = []
_TMP_STATE_DIR = tempfile.mkdtemp(prefix="ioc_test_state_")


def check(name, condition, detail=""):
    if condition:
        print(f"  [OK]   {name}")
    else:
        print(f"  [FAIL] {name}  {detail}")
        _failures.append(name)


def _make_controller(mode: str, api_configured: bool = True) -> AppController:
    """Создаёт контроллер с настроенным режимом (без чтения реального state file)."""
    ctl = AppController(_TMP_STATE_DIR)
    ctl.set_mode(mode)
    if api_configured:
        ctl.set_api_url("https://example.test/api")
        ctl.set_api_key("dummy-key")
    else:
        ctl.set_api_url("")
        ctl.set_api_key("")
    return ctl


def test_build_comments_fstec_uses_single_bulletin():
    print("\n== ФСТЭК: общий bulletin для всех IP ==")
    ctl = _make_controller("fstek")
    ctl.set_bulletin("FSTEC-2026-001")
    comments = ctl._build_ip_comments([
        ("1.1.1.1", "fileA.docx"),
        ("2.2.2.2", "fileB.docx"),
    ])
    check("оба IP имеют один bulletin",
          comments == {"1.1.1.1": "FSTEC-2026-001", "2.2.2.2": "FSTEC-2026-001"},
          f"got {comments}")


def test_build_comments_gossopka_per_file():
    print("\n== ГосСОПКА: per-file комментарии ==")
    ctl = _make_controller("gossopka")
    comments = ctl._build_ip_comments([
        ("1.1.1.1", "Бюллетень от 15.01.2026_42 НКЦКИ.docx"),
        ("2.2.2.2", "Бюллетень от 20.01.2026_77 ФинЦЕРТ.docx"),
    ])
    check("IP1 → НКЦКИ от 15.01.2026 (42)",
          comments.get("1.1.1.1") == "НКЦКИ от 15.01.2026 (42)",
          f"got {comments.get('1.1.1.1')!r}")
    check("IP2 → ФинЦЕРТ от 20.01.2026 (77)",
          comments.get("2.2.2.2") == "ФинЦЕРТ от 20.01.2026 (77)",
          f"got {comments.get('2.2.2.2')!r}")


def test_build_comments_gossopka_duplicate_ip_first_wins():
    print("\n== ГосСОПКА: дубликат IP из разных файлов → побеждает первый ==")
    ctl = _make_controller("gossopka")
    comments = ctl._build_ip_comments([
        ("1.1.1.1", "Бюллетень от 15.01.2026_42 НКЦКИ.docx"),
        ("1.1.1.1", "Бюллетень от 20.01.2026_77 ФинЦЕРТ.docx"),
    ])
    check("ровно один ключ",
          list(comments.keys()) == ["1.1.1.1"],
          f"got keys={list(comments.keys())}")
    check("значение от первого файла",
          comments["1.1.1.1"] == "НКЦКИ от 15.01.2026 (42)",
          f"got {comments['1.1.1.1']!r}")


def test_build_comments_gossopka_unparseable_fallback_to_stem():
    print("\n== ГосСОПКА: имя файла не по шаблону → fallback на stem ==")
    ctl = _make_controller("gossopka")
    comments = ctl._build_ip_comments([
        ("3.3.3.3", "произвольное_имя.docx"),
        ("4.4.4.4", ""),
    ])
    check("IP3 → 'произвольное_имя' (без расширения)",
          comments.get("3.3.3.3") == "произвольное_имя",
          f"got {comments.get('3.3.3.3')!r}")
    check("IP4 (пустой filename) → пустая строка",
          comments.get("4.4.4.4") == "",
          f"got {comments.get('4.4.4.4')!r}")


def test_send_ips_to_api_passes_per_ip_comments_to_sender():
    """Мокаем send_to_api, проверяем что в него уходит правильный dict."""
    print("\n== send_ips_to_api: payload в api_sender собран per-IP ==")
    ctl = _make_controller("gossopka")

    captured = {}

    def fake_send(ip_comments, api_url, api_key):
        captured["ip_comments"] = dict(ip_comments)
        captured["api_url"] = api_url
        captured["api_key"] = api_key
        return True, {ip: {"status": "OK", "text": "Успешно"} for ip in ip_comments}

    original = api_sender_module.send_to_api
    api_sender_module.send_to_api = fake_send
    try:
        result = ctl.send_ips_to_api([
            ("1.1.1.1", "Бюллетень от 15.01.2026_42 НКЦКИ.docx"),
            ("2.2.2.2", "Бюллетень от 20.01.2026_77 ФинЦЕРТ.docx"),
        ])
    finally:
        api_sender_module.send_to_api = original

    check("payload содержит оба IP",
          set(captured.get("ip_comments", {}).keys()) == {"1.1.1.1", "2.2.2.2"},
          f"got {captured}")
    check("каждый IP получил свой коммент",
          captured["ip_comments"]["1.1.1.1"] == "НКЦКИ от 15.01.2026 (42)"
          and captured["ip_comments"]["2.2.2.2"] == "ФинЦЕРТ от 20.01.2026 (77)",
          f"got {captured['ip_comments']}")
    check("результат с per-IP статусами вернулся",
          result.get("1.1.1.1", {}).get("status") == "OK"
          and result.get("2.2.2.2", {}).get("status") == "OK",
          f"got {result}")


def test_send_ips_to_api_no_config_short_circuits():
    print("\n== send_ips_to_api: без api_url/api_key — NO_CONFIG для всех ==")
    ctl = _make_controller("gossopka", api_configured=False)
    result = ctl.send_ips_to_api([
        ("1.1.1.1", "Бюллетень от 15.01.2026_42 НКЦКИ.docx"),
    ])
    check("статус NO_CONFIG",
          result.get("1.1.1.1", {}).get("status") == "NO_CONFIG",
          f"got {result}")


def test_send_ips_to_api_empty_returns_empty():
    print("\n== send_ips_to_api: пустой список — пустой результат ==")
    ctl = _make_controller("fstek")
    result = ctl.send_ips_to_api([])
    check("пустой dict",
          result == {},
          f"got {result}")


def main():
    tests = [
        test_build_comments_fstec_uses_single_bulletin,
        test_build_comments_gossopka_per_file,
        test_build_comments_gossopka_duplicate_ip_first_wins,
        test_build_comments_gossopka_unparseable_fallback_to_stem,
        test_send_ips_to_api_passes_per_ip_comments_to_sender,
        test_send_ips_to_api_no_config_short_circuits,
        test_send_ips_to_api_empty_returns_empty,
    ]
    for t in tests:
        t()

    print("\n" + "=" * 60)
    if _failures:
        print(f"FAILED: {len(_failures)}")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("ALL GREEN")


if __name__ == "__main__":
    main()
