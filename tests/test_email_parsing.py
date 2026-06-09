"""
Тесты email-парсинга: обфусцированные/чистые email, дубликаты, регрессии DNS.
"""

import pytest
from ioc_analyzer.core.parser import IOCParser


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


def test_fstec_obfuscated_email_with_dots_in_local():
    text = "Контакт: abc[.]qwe[.]123@mail[.]ru для связи."
    emails, dns = _run(text, "fstek")
    assert "abc.qwe.123@mail.ru" in emails
    assert "abc.qwe" not in dns


def test_fstec_duplicate_email():
    text = "Почта: abc[.]qwe[.]123@mail[.]ru. Повтор: abc[.]qwe[.]123@mail[.]ru."
    emails, dns = _run(text, "fstek")
    assert emails.count("abc.qwe.123@mail.ru") == 1
    assert len(emails) == 1
    assert not dns


def test_gossopka_mixed_email_with_dots_in_local():
    text = "Пиши на abc[.]qwe[.]123@mail[.]ru срочно."
    emails, dns = _run(text, "gossopka")
    assert "abc.qwe.123@mail.ru" in emails
    assert "abc.qwe" not in dns


def test_regression_fstec_plain_obfuscated_email():
    text = "user@example[.]com"
    emails, dns = _run(text, "fstek")
    assert "user@example.com" in emails
    assert not dns


def test_regression_gossopka_plain_email():
    text = "Контакт: user@example.com"
    emails, dns = _run(text, "gossopka")
    assert "user@example.com" in emails


def test_regression_dns_without_at():
    text = "Домен: bad[.]site[.]com — опасный."
    emails, dns = _run(text, "fstek")
    assert not emails
    assert "bad.site.com" in dns


def test_mixed_email_and_dns_in_one_line():
    text = "Пиши на a@b[.]ru, домен bad[.]com тоже вредный."
    emails, dns = _run(text, "fstek")
    assert "a@b.ru" in emails
    assert "bad.com" in dns
    assert "b" not in dns


def test_domain_before_email_in_text():
    text = "Сначала abc[.]qwe домен. Потом x[.]y[.]z@mail[.]ru почта."
    emails, dns = _run(text, "fstek")
    assert "x.y.z@mail.ru" in emails
    assert "abc.qwe" in dns
    assert "x.y.z" not in dns
