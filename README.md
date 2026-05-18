# BitScore — Modular Project Structure

Proyek ini adalah refactor dari `bitscore_app_fixed.py` menjadi arsitektur modular
berbasis fitur, sehingga 5 anggota tim bisa mengerjakan bagian masing-masing
tanpa konflik.

---

## Cara Menjalankan

```bash
pip install pillow requests python-dotenv
python main.py
```

---

## Struktur Folder

```
BITSCORE_MODULAR/
│
├── main.py                         # Entry point — jalankan ini
│
├── config/
│   ├── settings.py                 # API key, path, konstanta scraping
│   └── theme.py                    # Warna, font, helper UI (divider, dll)
│
├── models/
│   ├── game.py                     # Dataclass GameData
│   └── mapper.py                   # Konversi JSON → dict UI
│
├── scrapers/
│   ├── base.py                     # BaseScraper (HTTP session + retry)
│   ├── rawg.py                     # RAWG API scraper
│   ├── steam.py                    # Steam Store enrichment
│   ├── cheapshark.py               # CheapShark deal enrichment
│   └── pipeline.py                 # Orkestrasi: RAWG → Steam → CheapShark
│
├── store/
│   └── local_store.py              # Wishlist & Review (simpan ke disk JSON)
│
├── utils/
│   ├── helpers.py                  # strip_html, parse_reqs
│   ├── img_cache.py                # Two-level image cache (memory + disk)
│   └── spec_recommender.py         # SpecParser & SpecMatcher
│
└── ui/
    ├── app.py                      # Root window + navigasi + scraping
    ├── components/
    │   ├── game_card.py            # Komponen kartu game (list)
    │   └── dialogs.py              # ScrapeDialog & ReviewDialog
    └── pages/
        ├── home_page.py            # Halaman utama: daftar + filter + paginasi
        ├── detail_page.py          # Halaman detail: screenshot, info, review
        └── spec_page.py            # Halaman Spec Recommender
```

---

## Pembagian Tugas (5 Orang)

| Anggota | Modul yang Dikerjakan | Tanggung Jawab |
|---------|----------------------|----------------|
| **Anggota 1** | `scrapers/` | RAWG, Steam, CheapShark API — data fetching & enrichment |
| **Anggota 2** | `models/` + `store/` | Struktur data GameData, mapper JSON → UI, Wishlist & Reviews |
| **Anggota 3** | `ui/pages/home_page.py` | Halaman utama: kartu game, filter genre/platform, pagination |
| **Anggota 4** | `ui/pages/detail_page.py` | Halaman detail: screenshot viewer, tab info/reqs/review |
| **Anggota 5** | `ui/pages/spec_page.py` + `utils/spec_recommender.py` | Spec Recommender: input spek, parsing, matching, hasil |

> **Shared:** `config/`, `utils/helpers.py`, `utils/img_cache.py`, `ui/app.py`,
> dan `ui/components/` bisa dikerjakan bersama atau dibagi sesuai kebutuhan.

---

## Cara Kerja Antar Modul

```
main.py
  └─> ui/app.py  (BitScoreApp)
        ├─> ui/pages/home_page.py    (filter & daftar game)
        ├─> ui/pages/detail_page.py  (tampilan detail game)
        ├─> ui/pages/spec_page.py    (rekomendasi berdasar spek)
        ├─> ui/components/dialogs.py (ScrapeDialog, ReviewDialog)
        └─> scrapers/pipeline.py     (ambil data dari API)

scrapers/pipeline.py
  ├─> scrapers/rawg.py         → models/game.py (GameData)
  ├─> scrapers/steam.py        → enrich GameData
  └─> scrapers/cheapshark.py   → enrich harga/diskon

models/mapper.py
  └─> konversi GameData → dict UI yang dipakai semua halaman

store/local_store.py
  └─> wishlist.json + reviews.json (persist ke disk)

utils/img_cache.py
  └─> unduh & cache thumbnail (memory + img_cache/*.png)

utils/spec_recommender.py
  └─> SpecParser (parse teks requirements) + SpecMatcher (cocokkan spek user)
```

---

## Tips Pengembangan

- Setiap folder punya `__init__.py` dengan re-export, sehingga import bersih.
- Jangan ubah interface publik fungsi/kelas yang sudah dipakai modul lain
  tanpa koordinasi.
- `STORE` di `store/local_store.py` adalah singleton — langsung import dan pakai.
- `IMG` di `utils/img_cache.py` adalah singleton — langsung import dan pakai.
- Warna dan font selalu ambil dari `config/theme.py`, jangan hardcode.
