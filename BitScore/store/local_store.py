"""
store/local_store.py
====================
LocalStore: penyimpanan lokal untuk Wishlist dan Review pribadi.
"""

import json
from datetime import datetime
from config.settings import WISHLIST_JSON, REVIEWS_JSON


class LocalStore:
    def __init__(self):
        self._wl: set  = set()
        self._rv: dict = {}
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────
    def _load(self):
        if WISHLIST_JSON.exists():
            try:
                self._wl = set(json.loads(WISHLIST_JSON.read_text(encoding="utf-8")))
            except Exception:
                pass
        if REVIEWS_JSON.exists():
            try:
                self._rv = json.loads(REVIEWS_JSON.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save_wl(self):
        WISHLIST_JSON.write_text(
            json.dumps(list(self._wl), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _save_rv(self):
        REVIEWS_JSON.write_text(
            json.dumps(self._rv, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ── Wishlist ──────────────────────────────────────────────────────────────
    def in_wl(self, slug: str) -> bool:
        return slug in self._wl

    def toggle_wl(self, slug: str) -> bool:
        if self.in_wl(slug):
            self._wl.discard(slug)
        else:
            self._wl.add(slug)
        self._save_wl()
        return self.in_wl(slug)

    @property
    def wishlist(self) -> set:
        return self._wl

    # ── Reviews ───────────────────────────────────────────────────────────────
    def get_rv(self, slug: str) -> dict:
        return self._rv.get(slug, {"score": 0, "text": "", "date": ""})

    def set_rv(self, slug: str, score: int, text: str):
        self._rv[slug] = {
            "score": score,
            "text":  text,
            "date":  datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        self._save_rv()

    def del_rv(self, slug: str):
        self._rv.pop(slug, None)
        self._save_rv()

    def has_rv(self, slug: str) -> bool:
        return slug in self._rv

    @property
    def reviews(self) -> dict:
        return self._rv


# Singleton — dipakai oleh seluruh aplikasi
STORE = LocalStore()
