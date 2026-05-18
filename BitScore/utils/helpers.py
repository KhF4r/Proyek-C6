"""
utils/helpers.py
================
Fungsi-fungsi pembantu umum yang dipakai berbagai modul.
"""

import re


def strip_html(t: str) -> str:
    """Hapus tag HTML dan whitespace berlebih dari string."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or "")).strip()


def parse_reqs(text: str) -> list:
    """
    Parse teks requirements PC ke list tuple (key, value).
    key == '' berarti baris keterangan tanpa label.
    """
    lines = []
    raw = re.split(r'[\n\r]+|(?<=\w{3})  +', text)
    for part in raw:
        part = part.strip(" •*-–—")
        if not part:
            continue
        m = re.match(r'^([A-Z][A-Z0-9 /]{1,18}?)\s*:\s*(.+)$', part)
        if m:
            lines.append((m.group(1).strip().upper(), m.group(2).strip()))
        elif re.match(r'^[a-z].+:\s*.+', part, re.I):
            k, _, v = part.partition(":")
            lines.append((k.strip().upper(), v.strip()))
        else:
            lines.append(("", part))
    return lines
