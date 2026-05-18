"""
ui/components/game_card.py
==========================
Komponen kartu game untuk daftar utama (Home & Wishlist & My Reviews).
"""

import tkinter as tk
import tkinter.font as tkfont

from config.theme import (
    BG_CARD, BG_CARD_HVR, BORDER2, ACCENT_LIGHT, ACCENT_BG, ACCENT_DIM,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED, AMBER, AMBER_BG, GREEN, GREEN_BG,
    GREEN_DIM, FREE_GREEN, WARN_ORANGE, RED_COL, RED_BG,
    GOLD_BADGE, SILVER_BADGE, BRONZE_BADGE, TEAL,
    F, FM, meta_color, review_color,
)
from config.settings import COVER_W, COVER_H
from store.local_store import STORE
from utils.img_cache import IMG


def build_card(parent, game: dict, rank: int, open_detail_cb,
               show_rank=True, show_rv=False):
    """
    Buat satu baris kartu game dan pack ke parent.

    Parameters
    ----------
    parent        : tk.Frame  — container tempat kartu di-pack
    game          : dict      — data game (hasil mapper)
    rank          : int       — nomor urut (#1, #2, ...)
    open_detail_cb: callable  — dipanggil saat kartu diklik
    show_rank     : bool      — tampilkan badge #rank
    show_rv       : bool      — tampilkan bintang review
    """
    rc_map = {1: GOLD_BADGE, 2: SILVER_BADGE, 3: BRONZE_BADGE}
    stripe = rc_map.get(rank, ACCENT_DIM) if show_rank else TEAL
    is_wl  = STORE.in_wl(game["slug"])

    outer = tk.Frame(parent, bg=BORDER2)
    outer.pack(fill="x", pady=3, padx=14)
    card = tk.Frame(outer, bg=BG_CARD, cursor="hand2")
    card.pack(fill="x", padx=1, pady=1)

    def hover_on(e):      _rc(card, BG_CARD_HVR)
    def hover_off(e):     _rc(card, BG_CARD)
    def open_det(e=None): open_detail_cb(game)
    card.bind("<Enter>", hover_on)
    card.bind("<Leave>", hover_off)
    card.bind("<Button-1>", open_det)

    card.columnconfigure(3, weight=1)
    card.columnconfigure(4, minsize=200, weight=0)

    # Accent stripe
    tk.Frame(card, bg=stripe, width=4).grid(row=0, column=0, sticky="ns")

    # Rank badge
    col_start = 1
    if show_rank:
        rf = tk.Frame(card, bg=BG_CARD, width=48)
        rf.grid(row=0, column=1, sticky="ns")
        rf.grid_propagate(False)
        tk.Label(rf, text=f"#{rank}", font=FM(11, True),
                 fg=rc_map.get(rank, TEXT_MUTED), bg=BG_CARD).pack(expand=True)
        col_start = 2

    # Thumbnail
    tf = tk.Frame(card, bg=game["color"], width=COVER_W, height=COVER_H,
                  highlightthickness=1, highlightbackground=BORDER2)
    tf.grid(row=0, column=col_start, padx=(6, 0), pady=8, sticky="w")
    tf.grid_propagate(False)
    cv = tk.Canvas(tf, width=COVER_W, height=COVER_H, bg=game["color"], highlightthickness=0)
    cv.place(x=0, y=0)
    cv.create_text(COVER_W // 2, COVER_H // 2, text=game["title"][0].upper(),
                   font=FM(28, True), fill=TEXT_MUTED)

    def _sc(img, c=cv):
        if img:
            c._img = img
            c.delete("all")
            c.create_image(0, 0, anchor="nw", image=img)

    IMG.get(game["cover_url"], size=(COVER_W, COVER_H),
            cb=lambda img, fn=_sc: card.after(0, fn, img))

    # Info block
    inf = tk.Frame(card, bg=BG_CARD)
    inf.grid(row=0, column=col_start + 1, sticky="nsew", padx=14, pady=10)

    tk.Label(inf, text=game["title"], font=F(13, True),
             fg=TEXT_WHITE, bg=BG_CARD, anchor="w").pack(fill="x")

    if game["genres"]:
        gr = tk.Frame(inf, bg=BG_CARD)
        gr.pack(anchor="w", pady=(5, 0))
        for gn in game["genres"][:3]:
            tk.Label(gr, text=gn, font=F(8), fg=ACCENT_LIGHT, bg=ACCENT_BG,
                     padx=6, pady=2).pack(side="left", padx=(0, 4))

    if game["platforms"]:
        plats = game["platforms"][:4]
        pt = "  ·  ".join(plats)
        if len(game["platforms"]) > 4:
            pt += f"  +{len(game['platforms'])-4}"
        tk.Label(inf, text=pt, font=F(8), fg=TEXT_MUTED, bg=BG_CARD, anchor="w").pack(anchor="w", pady=(4, 0))

    # Scores row
    rr = tk.Frame(inf, bg=BG_CARD)
    rr.pack(anchor="w", pady=(7, 0))

    rb = tk.Frame(rr, bg=AMBER_BG, highlightthickness=1, highlightbackground="#3a2a06")
    rb.pack(side="left", padx=(0, 6))
    tk.Label(rb, text=f"\u2605  {game['rating']:.2f}", font=FM(11, True),
             fg=AMBER, bg=AMBER_BG, padx=9, pady=4).pack()

    mc = game.get("metacritic")
    if mc:
        mb = tk.Frame(rr, bg=GREEN_BG, highlightthickness=1, highlightbackground=GREEN_DIM)
        mb.pack(side="left", padx=(0, 6))
        tk.Label(mb, text=f"MC  {mc}", font=FM(10, True),
                 fg=meta_color(mc), bg=GREEN_BG, padx=8, pady=4).pack()

    sr = game.get("review", "")
    if sr and sr not in ("", "N/A"):
        src = GREEN if "Positive" in sr else (AMBER if "Mixed" in sr else RED_COL)
        tk.Label(rr, text=sr, font=F(8), fg=src, bg=BG_CARD, padx=4).pack(side="left")

    pr_c = FREE_GREEN if game["is_free"] else (
           WARN_ORANGE if game.get("deal_price") else (
           ACCENT_LIGHT if game["price"] not in ("N/A", "") else TEXT_MUTED))
    price_txt = "FREE" if game["is_free"] else game["price"]
    if game.get("deal_savings"):
        price_txt += f"  -{game['deal_savings']}"
    tk.Label(rr, text=price_txt, font=F(9, True), fg=pr_c, bg=BG_CARD, padx=6).pack(side="left")

    wl_c = AMBER if is_wl else TEXT_MUTED
    tk.Label(rr, text="\u2665", font=F(13), fg=wl_c, bg=BG_CARD, padx=2).pack(side="left")

    if show_rv and STORE.has_rv(game["slug"]):
        rv    = STORE.get_rv(game["slug"])
        stars = "\u2605" * rv["score"] + "\u2606" * (5 - rv["score"])
        tk.Label(inf, text=f"Your review: {stars}", font=F(9),
                 fg=AMBER, bg=BG_CARD).pack(anchor="w", pady=(3, 0))

    # Right meta
    rc2 = tk.Frame(card, bg=BG_CARD, width=200)
    rc2.grid(row=0, column=col_start + 2, sticky="nse", padx=(0, 14), pady=10)
    rc2.grid_propagate(False)

    tk.Label(rc2, text=game["developer"], font=F(9), fg=TEXT_DIM,
             bg=BG_CARD, anchor="e", wraplength=188, justify="right").pack(anchor="e")
    age = game.get("age_rating", "")
    if age and str(age).strip() not in ("", "0"):
        af = tk.Frame(rc2, bg=RED_BG, highlightthickness=1, highlightbackground=RED_COL)
        af.pack(anchor="e", pady=(4, 0))
        tk.Label(af, text=age, font=F(8, True), fg=RED_COL, bg=RED_BG, padx=6, pady=2).pack()
    if game["review"]:
        tk.Label(rc2, text=game["review"], font=F(8),
                 fg=review_color(game["review"]), bg=BG_CARD,
                 anchor="e", wraplength=188, justify="right").pack(anchor="e", pady=(4, 0))
    if game["rawg_count"]:
        tk.Label(rc2, text=f"{game['rawg_count']:,} ratings", font=F(8),
                 fg=TEXT_MUTED, bg=BG_CARD, anchor="e").pack(anchor="e", pady=(3, 0))

    # Bind hover & click to all child widgets
    for w in [card, inf, rc2, tf, cv]:
        try:
            w.bind("<Enter>", hover_on)
            w.bind("<Leave>", hover_off)
            w.bind("<Button-1>", open_det)
        except Exception:
            pass
    for ch in list(inf.winfo_children()) + list(rc2.winfo_children()):
        try:
            ch.bind("<Enter>", hover_on)
            ch.bind("<Leave>", hover_off)
            ch.bind("<Button-1>", open_det)
        except Exception:
            pass


def _rc(w, c):
    """Rekursif ganti background widget dan semua child-nya."""
    try:
        if w.winfo_class() != "Canvas":
            w.configure(bg=c)
    except Exception:
        pass
    for ch in w.winfo_children():
        _rc(ch, c)
