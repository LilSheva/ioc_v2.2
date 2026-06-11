"""S/MIME utilities for workstation test mode (-tst)."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from email import message_from_bytes
from email.header import decode_header
from email.message import Message

PKCS7_MIME_TYPES = {"application/pkcs7-mime", "application/x-pkcs7-mime"}
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_PS_DECRYPT_SCRIPT = """\
param([string]$In, [string]$Out)
Add-Type -AssemblyName System.Security
$data = [System.IO.File]::ReadAllBytes($In)
for ($i = 0; $i -lt 10; $i++) {
    $unwrapped = $false
    try {
        $env = New-Object System.Security.Cryptography.Pkcs.EnvelopedCms
        $env.Decode($data)
        $env.Decrypt()
        $data = $env.ContentInfo.Content
        $unwrapped = $true
    } catch {}
    if (-not $unwrapped) {
        try {
            $sig = New-Object System.Security.Cryptography.Pkcs.SignedCms
            $sig.Decode($data)
            $data = $sig.ContentInfo.Content
            $unwrapped = $true
        } catch {}
    }
    if (-not $unwrapped) { break }
}
[System.IO.File]::WriteAllBytes($Out, $data)
"""


def is_smime_filename(name: str) -> bool:
    return (name or "").strip().lower() == "smime.p7m"


def extract_smime_attachments(
    encrypted_content: bytes,
    dest_dir: str,
    logger: logging.Logger,
    max_depth: int = 6,
) -> list[str]:
    decrypted = _decrypt_smime_windows(encrypted_content, logger)
    if not decrypted:
        return []
    extracted = _extract_from_mime(
        decrypted,
        dest_dir=dest_dir,
        logger=logger,
        depth=0,
        max_depth=max_depth,
    )
    if extracted:
        return extracted
    logger.warning(
        "smime.p7m расшифрован, но вложения не найдены в MIME-структуре. Структура письма: %s",
        describe_mime_structure(decrypted),
    )
    return []


def _decrypt_smime_windows(content: bytes, logger: logging.Logger) -> bytes | None:
    tmp_dir = tempfile.mkdtemp(prefix="smime_")
    in_path = os.path.join(tmp_dir, "in.p7m")
    out_path = os.path.join(tmp_dir, "out.bin")
    ps_path = os.path.join(tmp_dir, "decrypt.ps1")
    try:
        with open(in_path, "wb") as f:
            f.write(content)
        with open(ps_path, "w", encoding="utf-8") as f:
            f.write(_PS_DECRYPT_SCRIPT)
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                ps_path,
                "-In",
                in_path,
                "-Out",
                out_path,
            ],
            capture_output=True,
            timeout=45,
        )
        if result.returncode != 0:
            stderr = (result.stderr or b"").decode("utf-8", errors="replace").strip()
            logger.warning("S/MIME decrypt via PowerShell failed: %s", stderr or "(no output)")
            return None
        if not os.path.exists(out_path):
            logger.warning("S/MIME decrypt returned success, but output is missing.")
            return None
        with open(out_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.warning("S/MIME decrypt error: %s", e)
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _extract_from_mime(
    mime_bytes: bytes,
    dest_dir: str,
    logger: logging.Logger,
    depth: int,
    max_depth: int,
) -> list[str]:
    if depth > max_depth:
        logger.warning("smime: достигнут max_depth=%s при разборе MIME.", max_depth)
        return []
    try:
        msg = message_from_bytes(mime_bytes)
    except Exception as e:
        logger.warning("MIME parse failed: %s", e)
        return []

    extracted: list[str] = []
    for part in msg.walk():
        ctype = (part.get_content_type() or "").lower()
        try:
            if ctype in PKCS7_MIME_TYPES:
                inner = part.get_payload(decode=True)
                if inner:
                    logger.info("smime: вложенный PKCS7-слой, разворачиваем...")
                    nested = _decrypt_smime_windows(inner, logger)
                    if nested:
                        extracted.extend(
                            _extract_from_mime(
                                nested,
                                dest_dir=dest_dir,
                                logger=logger,
                                depth=depth + 1,
                                max_depth=max_depth,
                            )
                        )
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            name = _resolve_part_filename(part)
            if not name and ctype == DOCX_MIME_TYPE:
                name = f"attachment_{depth}_{len(extracted)+1}.docx"
            if not name:
                disposition = (part.get_content_disposition() or "").lower()
                if disposition != "attachment":
                    continue
                name = f"attachment_{depth}_{len(extracted)+1}.bin"
            safe_name = _sanitize_filename(name)
            dest = _write_unique_file(dest_dir, safe_name, payload)
            extracted.append(dest)
            logger.info("   Извлечено из S/MIME: %s (%d байт)", os.path.basename(dest), len(payload))
        except Exception as e:
            logger.warning("MIME part skip (type=%s): %s", ctype, e)
    return extracted


def _resolve_part_filename(part: Message) -> str:
    raw_name = (
        part.get_filename()
        or part.get_param("name")
        or part.get_param("name", header="content-type")
        or ""
    )
    return _decode_mime_filename(str(raw_name)) if raw_name else ""


def _decode_mime_filename(raw: str) -> str:
    try:
        chunks = decode_header(raw)
    except Exception:
        chunks = [(raw, None)]
    out: list[str] = []
    for chunk, charset in chunks:
        if isinstance(chunk, bytes):
            try:
                out.append(chunk.decode(charset or "utf-8", errors="replace"))
            except Exception:
                out.append(chunk.decode("utf-8", errors="replace"))
        else:
            out.append(str(chunk))
    name = "".join(out).replace("\r", "").replace("\n", "").replace("\t", " ")
    return re.sub(r"\s+", " ", name).strip()


def _sanitize_filename(name: str) -> str:
    base = os.path.basename(name)
    base = re.sub(r"[\x00-\x1f]", "", base)
    base = re.sub(r'[\\/*?:"<>|]', "_", base).strip(" .")
    return base or "attachment.bin"


def _write_unique_file(dest_dir: str, filename: str, payload: bytes) -> str:
    root, ext = os.path.splitext(filename)
    candidate = os.path.join(dest_dir, filename)
    index = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dest_dir, f"{root}_{index}{ext}")
        index += 1
    with open(candidate, "wb") as f:
        f.write(payload)
    return candidate


def describe_mime_structure(mime_bytes: bytes) -> str:
    try:
        msg = message_from_bytes(mime_bytes)
    except Exception:
        return f"(не MIME, первые байты: {mime_bytes[:40]!r})"
    parts: list[str] = []
    for part in msg.walk():
        name = part.get_filename() or part.get_param("name") or ""
        parts.append(f"{part.get_content_type()}(name={name!r})")
    return "; ".join(parts) or "(пусто)"

