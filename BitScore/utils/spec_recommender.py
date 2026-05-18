"""
utils/spec_recommender.py
=========================
SpecParser & SpecMatcher: parsing spesifikasi PC dan pencocokan dengan game.
"""

import re
from typing import Optional


class SpecParser:
    """Parse teks requirements PC ke nilai numerik yang bisa dibandingkan."""

    @staticmethod
    def extract_ram_gb(text: str) -> Optional[int]:
        text = text.lower()
        m = re.search(r'(\d+)\s*gb\s*(?:ram|memory|memori)', text)
        if m: return int(m.group(1))
        m = re.search(r'(?:ram|memory|memori)[:\s]+(\d+)\s*gb', text)
        if m: return int(m.group(1))
        m = re.search(r'(\d+)\s*gb', text)
        if m: return int(m.group(1))
        return None

    @staticmethod
    def extract_cpu_tier(text: str) -> int:
        """Return CPU tier 1-10."""
        text = text.lower()
        tiers = [
            (10, ["i9-13", "i9-12", "i9-11", "ryzen 9 7", "ryzen 9 5"]),
            (9,  ["i9-10", "i9-9",  "ryzen 9 3", "ryzen 7 7", "i7-13", "i7-12"]),
            (8,  ["i7-11", "i7-10", "i7-9", "ryzen 7 5", "ryzen 7 3"]),
            (7,  ["i7-8",  "i7-7",  "ryzen 5 7", "ryzen 5 5600"]),
            (6,  ["i5-12", "i5-11", "i5-10", "ryzen 5 3600", "ryzen 5 3"]),
            (5,  ["i5-9",  "i5-8",  "i5-7", "ryzen 5 2", "ryzen 5 1"]),
            (4,  ["i5-6",  "i5-4",  "i5-3", "i5-2", "ryzen 3 3", "ryzen 3 2"]),
            (3,  ["i3-10", "i3-9",  "i3-8", "ryzen 3 1"]),
            (2,  ["i3-7",  "i3-6",  "i3-4", "i3-3", "i3-2", "fx-8", "fx-6"]),
            (1,  ["i3-1",  "pentium", "celeron", "athlon", "fx-4", "fx-2"]),
        ]
        for tier, keywords in tiers:
            for kw in keywords:
                if kw in text: return tier
        m = re.search(r'i[3579]-(\d{4,5})', text)
        if m:
            gen = int(m.group(1)[:2] if len(m.group(1)) >= 4 else m.group(1)[0])
            return min(max(gen, 1), 8)
        return 0

    @staticmethod
    def extract_vram_gb(text: str) -> Optional[int]:
        text = text.lower()
        m = re.search(r'(\d+)\s*gb\s*(?:vram|video\s*memory|dedicated)', text)
        return int(m.group(1)) if m else None

    @staticmethod
    def extract_gpu_tier(text: str) -> int:
        """Return GPU tier 1-10."""
        text = text.lower()
        tiers = [
            (10, ["rtx 4090", "rtx 4080", "rx 7900"]),
            (9,  ["rtx 4070", "rtx 4060 ti", "rtx 3090", "rtx 3080", "rx 6900", "rx 6800"]),
            (8,  ["rtx 3070", "rtx 3060 ti", "rx 6700", "rx 6600 xt", "rtx 4060"]),
            (7,  ["rtx 3060", "rtx 2070", "rtx 2080", "rx 6600", "rx 5700"]),
            (6,  ["rtx 2060", "gtx 1080 ti", "gtx 1080", "rx 5600", "rx 5500"]),
            (5,  ["gtx 1070 ti", "gtx 1070", "rtx 2060 super", "rx 580", "rx 590", "rx 5500 xt"]),
            (4,  ["gtx 1060", "rx 480", "rx 570", "gtx 980", "gtx 970"]),
            (3,  ["gtx 1050 ti", "gtx 1050", "rx 470", "rx 460", "gtx 960", "gtx 950"]),
            (2,  ["gtx 750 ti", "gtx 750", "r9 270", "r9 280", "gtx 760", "gtx 770"]),
            (1,  ["gtx 650", "gtx 660", "r7 260", "r9 255", "intel hd", "intel uhd", "iris"]),
        ]
        for tier, keywords in tiers:
            for kw in keywords:
                if kw in text: return tier
        vram = SpecParser.extract_vram_gb(text)
        if vram:
            if vram >= 12: return 8
            if vram >= 8:  return 7
            if vram >= 6:  return 6
            if vram >= 4:  return 5
            if vram >= 2:  return 3
            return 2
        return 0


class SpecMatcher:
    """Bandingkan spek user dengan requirements game."""

    GPU_USER_MAP = {
        "rtx 4090": 10, "rtx 4080": 10, "rtx 4070 ti": 9, "rtx 4070": 9,
        "rtx 4060 ti": 8, "rtx 4060": 8,
        "rtx 3090": 9, "rtx 3080 ti": 9, "rtx 3080": 9, "rtx 3070 ti": 8,
        "rtx 3070": 8, "rtx 3060 ti": 8, "rtx 3060": 7,
        "rtx 2080 ti": 7, "rtx 2080": 7, "rtx 2070 super": 7, "rtx 2070": 7,
        "rtx 2060 super": 6, "rtx 2060": 6,
        "gtx 1080 ti": 6, "gtx 1080": 6, "gtx 1070 ti": 5, "gtx 1070": 5,
        "gtx 1060": 4, "gtx 1050 ti": 3, "gtx 1050": 3,
        "rx 7900 xtx": 10, "rx 7900 xt": 10, "rx 6900 xt": 9, "rx 6800 xt": 9,
        "rx 6800": 9, "rx 6700 xt": 8, "rx 6600 xt": 8, "rx 6600": 7,
        "rx 5700 xt": 7, "rx 5700": 7, "rx 5600 xt": 6, "rx 5500 xt": 5,
        "rx 580": 5, "rx 570": 4, "rx 480": 5, "rx 470": 4, "rx 460": 3,
        "intel arc a770": 7, "intel arc a750": 6, "intel arc a380": 4,
        "intel hd": 1, "intel uhd 620": 1, "intel uhd 630": 1,
        "iris xe": 2, "iris plus": 1, "gt 1030": 2, "gt 730": 1,
    }

    CPU_USER_MAP = {
        "i9-13900": 10, "i9-12900": 10, "i9-11900": 9,
        "i9-10900": 9,  "i9-9900": 9,
        "i7-13700": 9,  "i7-12700": 9, "i7-11700": 8, "i7-10700": 8,
        "i7-9700": 8,   "i7-8700": 8,  "i7-7700": 7,  "i7-6700": 6,
        "i5-13600": 8,  "i5-12600": 7, "i5-11600": 7, "i5-10600": 6,
        "i5-10400": 6,  "i5-9600": 6,  "i5-9400": 5,  "i5-8600": 5,
        "i5-8400": 5,   "i5-7400": 4,  "i5-6600": 4,  "i5-4690": 3,
        "i3-12100": 6,  "i3-10100": 5, "i3-9100": 4,  "i3-8100": 4,
        "i3-7100": 3,   "i3-6100": 3,
        "ryzen 9 7950": 10, "ryzen 9 7900": 10, "ryzen 9 5950": 10,
        "ryzen 9 5900": 9,  "ryzen 9 3900": 9,
        "ryzen 7 7700": 9,  "ryzen 7 5800": 8, "ryzen 7 5700": 8,
        "ryzen 7 3700": 8,  "ryzen 7 2700": 7,
        "ryzen 5 7600": 8,  "ryzen 5 5600": 7, "ryzen 5 3600": 7,
        "ryzen 5 2600": 6,  "ryzen 5 1600": 5,
        "ryzen 3 4300": 5,  "ryzen 3 3300": 4, "ryzen 3 3100": 4,
        "ryzen 3 2200": 3,
    }

    @classmethod
    def user_gpu_tier(cls, gpu_str: str) -> int:
        gpu_lower = gpu_str.strip().lower()
        for key, tier in cls.GPU_USER_MAP.items():
            if key in gpu_lower: return tier
        t = SpecParser.extract_gpu_tier(gpu_lower)
        return t if t > 0 else 4

    @classmethod
    def user_cpu_tier(cls, cpu_str: str) -> int:
        cpu_lower = cpu_str.strip().lower()
        for key, tier in cls.CPU_USER_MAP.items():
            if key in cpu_lower: return tier
        t = SpecParser.extract_cpu_tier(cpu_lower)
        return t if t > 0 else 4

    @classmethod
    def _cmp(cls, user_val, req_val, is_ram=False):
        if req_val is None or req_val == 0: return "yes"
        if is_ram:
            r = user_val / req_val
            return "yes" if r >= 1.0 else ("maybe" if r >= 0.75 else "no")
        d = user_val - req_val
        return "yes" if d >= 0 else ("maybe" if d >= -1 else "no")

    @classmethod
    def check_game(cls, game: dict, user_ram: int, user_cpu_tier: int, user_gpu_tier: int) -> str:
        """Return: 'smooth' | 'maybe' | 'heavy' | 'unknown'."""
        min_txt = (game.get("pc_minimum") or "").lower()
        rec_txt = (game.get("pc_recommended") or "").lower()
        if not min_txt and not rec_txt: return "unknown"

        min_ram = SpecParser.extract_ram_gb(min_txt)
        min_cpu = SpecParser.extract_cpu_tier(min_txt)
        min_gpu = SpecParser.extract_gpu_tier(min_txt)
        rec_ram = SpecParser.extract_ram_gb(rec_txt)
        rec_cpu = SpecParser.extract_cpu_tier(rec_txt)
        rec_gpu = SpecParser.extract_gpu_tier(rec_txt)

        parseable = sum(1 for v in [min_ram, min_cpu, min_gpu, rec_ram, rec_cpu, rec_gpu]
                        if v not in (None, 0))
        if parseable == 0: return "unknown"

        rec_checks = []
        if rec_ram is not None: rec_checks.append(cls._cmp(user_ram, rec_ram, True))
        if rec_cpu != 0:        rec_checks.append(cls._cmp(user_cpu_tier, rec_cpu))
        if rec_gpu != 0:        rec_checks.append(cls._cmp(user_gpu_tier, rec_gpu))
        if rec_checks and all(v == "yes" for v in rec_checks): return "smooth"

        min_checks = []
        if min_ram is not None: min_checks.append(cls._cmp(user_ram, min_ram, True))
        if min_cpu != 0:        min_checks.append(cls._cmp(user_cpu_tier, min_cpu))
        if min_gpu != 0:        min_checks.append(cls._cmp(user_gpu_tier, min_gpu))

        if not min_checks:
            return "maybe" if (rec_checks and not any(v == "no" for v in rec_checks)) else "heavy"
        fails = [v for v in min_checks if v == "no"]
        return "maybe" if not fails else "heavy"
