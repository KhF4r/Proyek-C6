"""
utils/img_cache.py
==================
ImgCache: two-level cache (memory + disk) untuk thumbnail game.
"""

import threading
import hashlib
from io import BytesIO
from urllib.request import urlopen, Request

from config.settings import IMG_CACHE_DIR, COVER_W, COVER_H

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImgCache:
    """
    Cache gambar dua lapisan: memori (dict) + disk (PNG).
    - Request pertama: unduh, simpan ke disk, cache di memori.
    - Request berikutnya: langsung dari memori atau muat dari disk.
    """

    def __init__(self):
        self._mem  = {}
        self._lock = threading.Lock()
        self._cbs  = {}

    def get(self, url, size=(COVER_W, COVER_H), cb=None):
        if not url:
            return None
        key = self._key(url, size)
        with self._lock:
            if key in self._mem:
                img = self._mem[key]
                if cb and img:
                    cb(img)
                return img
            self._cbs.setdefault(key, [])
            if cb:
                self._cbs[key].append(cb)
            if len(self._cbs[key]) <= 1:
                threading.Thread(target=self._fetch, args=(url, size, key), daemon=True).start()
        return None

    @staticmethod
    def _key(url, size):
        return hashlib.md5(f"{url}|{size[0]}x{size[1]}".encode()).hexdigest()

    @staticmethod
    def _disk_path(key):
        return IMG_CACHE_DIR / f"{key}.png"

    def _fetch(self, url, size, key):
        img = None
        if PIL_AVAILABLE:
            disk = self._disk_path(key)
            try:
                if disk.exists():
                    pil = Image.open(disk).convert("RGB")
                    if pil.size != size:
                        pil.thumbnail(size, Image.LANCZOS)
                        bg  = Image.new("RGB", size, (17, 15, 28))
                        off = ((size[0] - pil.width) // 2, (size[1] - pil.height) // 2)
                        bg.paste(pil, off)
                        pil = bg
                else:
                    req = Request(url, headers={"User-Agent": "BitScore/4.0"})
                    raw = urlopen(req, timeout=8).read()
                    pil = Image.open(BytesIO(raw)).convert("RGBA")
                    pil.thumbnail(size, Image.LANCZOS)
                    bg  = Image.new("RGB", size, (17, 15, 28))
                    off = ((size[0] - pil.width) // 2, (size[1] - pil.height) // 2)
                    bg.paste(pil, off, pil if pil.mode == "RGBA" else None)
                    pil = bg
                    try:
                        pil.save(disk, "PNG", optimize=True, compress_level=6)
                    except Exception:
                        pass
                img = ImageTk.PhotoImage(pil)
            except Exception:
                pass

        with self._lock:
            self._mem[key] = img
            cbs = self._cbs.pop(key, [])
        for fn in cbs:
            if fn:
                fn(img)

    def clear_disk_cache(self):
        for f in IMG_CACHE_DIR.glob("*.png"):
            try:
                f.unlink()
            except Exception:
                pass
        with self._lock:
            self._mem.clear()


# Singleton image cache
IMG = ImgCache()
