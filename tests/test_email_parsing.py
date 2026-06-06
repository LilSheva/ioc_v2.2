"""Тесты email-парсинга: обфусцированные/чистые email, дубликаты, регрессии DNS.

Запуск: python -m tests.test_email_parsing   или   python tests/test_email_parsing.py
Тесты печатают результаты в stdout — это dev-скрипт, не попадает в .exe-сборку.
"""
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model.ioc_parser_v21_fixed import IOCParser  # type: ignore


def _minimal_config():
    return [
        {
            "enabled": True,
            "name": "Email",
            "regex": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
            "blacklist": [],
            "exclusions": [],
        },
        {
            "enabled": True,
            "name": "DNS",
            "regex": r"\b[a-zA-Z0-9-]+(?:\[\.\][a-zA-Z0-9-]+)+\b",
            "blacklist": [],
            "exclusions": [],
        },
        {
            "enabled": True,
            "name": "IP",
            "regex": r"\b(?:\d{1,3}\[\.\]){3}\d{1,3}\b",
            "blacklist": [],
            "exclusions": [],
        },
    ]


def _run(text: str, mode: str):
    parser = IOCParser(_minimal_config(), mode=mode)
    res = parser.find_all_raw_matches(text)
    emails = [c for _, c in res.get('Email', [])]
    dns = [c for _, c in res.get('DNS', [])]
    return emails, dns


_failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"  [OK]   {name}")
    else:
        print(f"  [FAIL] {name}  {detail}")
        _failures.append(name)


def test_fstec_obfuscated_email_with_dots_in_local():
    print("\n== FSTEC: obfuscated email with [.] in local-part ==")
    text = "Контакт: abc[.]qwe[.]123@mail[.]ru для связи."
    emails, dns = _run(text, "fstek")
    check("email содержит полный адрес с abc.qwe.123",
          any("abc.qwe.123@mail.ru" == e for e in emails),
          f"got emails={emails}")
    check("DNS не захватил abc.qwe как домен",
          "abc.qwe" not in dns,
          f"got dns={dns}")


def test_fstec_duplicate_email():
    print("\n== FSTEC: duplicate obfuscated email ==")
    text = "Почта: abc[.]qwe[.]123@mail[.]ru. Повтор: abc[.]qwe[.]123@mail[.]ru."
    emails, dns = _run(text, "fstek")
    check("после дедупа ровно 1 cleaned email",
          emails.count("abc.qwe.123@mail.ru") == 1 and len(emails) == 1,
          f"got emails={emails}")
    check("DNS пуст",
          dns == [],
          f"got dns={dns}")


def test_gossopka_mixed_email_with_dots_in_local():
    print("\n== GOSSOPKA: obfuscated email with [.] in local-part ==")
    text = "Пиши на abc[.]qwe[.]123@mail[.]ru срочно."
    emails, dns = _run(text, "gossopka")
    check("email = abc.qwe.123@mail.ru",
          "abc.qwe.123@mail.ru" in emails,
          f"got emails={emails}")
    check("DNS не захватил abc.qwe",
          "abc.qwe" not in dns,
          f"got dns={dns}")


def test_regression_fstec_plain_obfuscated_email():
    print("\n== REGR FSTEC: обычный обфусцированный email без точек в local ==")
    text = "user@example[.]com"
    emails, dns = _run(text, "fstek")
    check("email = user@example.com",
          "user@example.com" in emails,
          f"got emails={emails}")
    check("DNS пуст",
          dns == [],
          f"got dns={dns}")


def test_regression_gossopka_plain_email():
    print("\n== REGR GOSSOPKA: чистый (необфусцированный) email ==")
    text = "Контакт: user@example.com"
    emails, dns = _run(text, "gossopka")
    check("email = user@example.com",
          "user@example.com" in emails,
          f"got emails={emails}")


def test_regression_dns_without_at():
    print("\n== REGR: DNS без @ остаётся DNS ==")
    text = "Домен: bad[.]site[.]com — опасный."
    emails, dns = _run(text, "fstek")
    check("email пуст",
          emails == [],
          f"got emails={emails}")
    check("DNS содержит bad.site.com",
          "bad.site.com" in dns,
          f"got dns={dns}")


def test_mixed_email_and_dns_in_one_line():
    print("\n== Email + DNS рядом в одной строке ==")
    text = "Пиши на a@b[.]ru, домен bad[.]com тоже вредный."
    emails, dns = _run(text, "fstek")
    check("email содержит a@b.ru",
          "a@b.ru" in emails,
          f"got emails={emails}")
    check("DNS содержит bad.com и не содержит b (от email)",
          "bad.com" in dns and "b" not in dns,
          f"got dns={dns}")


def test_domain_before_email_in_text():
    print("\n== Отдельный DNS в тексте + email дальше ==")
    text = "Сначала abc[.]qwe домен. Потом x[.]y[.]z@mail[.]ru почта."
    emails, dns = _run(text, "fstek")
    check("email x.y.z@mail.ru найден",
          "x.y.z@mail.ru" in emails,
          f"got emails={emails}")
    check("DNS abc.qwe найден (без @ рядом — это реальный домен)",
          "abc.qwe" in dns,
          f"got dns={dns}")
    check("DNS x.y.z НЕ захвачен (поглощён email)",
          "x.y.z" not in dns,
          f"got dns={dns}")


def main():
    tests = [
        test_fstec_obfuscated_email_with_dots_in_local,
        test_fstec_duplicate_email,
        test_gossopka_mixed_email_with_dots_in_local,
        test_regression_fstec_plain_obfuscated_email,
        test_regression_gossopka_plain_email,
        test_regression_dns_without_at,
        test_mixed_email_and_dns_in_one_line,
        test_domain_before_email_in_text,
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
