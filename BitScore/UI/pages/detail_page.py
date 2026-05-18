"""
ui/pages/detail_page.py
=======================
Halaman detail game: screenshot viewer, info panel, PC Requirements, dan Review tab.
"""

import webbrowser
from io import BytesIO
from urllib.request import urlopen, Request

import tkinter as tk
import tkinter.ttk as ttk

from config.settings import COVER_W, COVER_H
from config.theme import (
    BG_DEEP, BG_PANEL, BG_CARD, BG_SURFACE2, BG_SURFACE3,
    BORDER2, ACCENT, ACCENT_LIGHT, ACCENT_BG, ACCENT_DIM,
    GREEN, GREEN_BG, GREEN_DIM, AMBER, AMBER_BG, RED_COL, RED_BG,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED,
    FREE_GREEN, WARN_ORANGE,
    F, FM, divider, review_color, meta_color,
)
from store.local_store import STORE
from utils.img_cache import IMG
from utils.helpers import parse_reqs

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

SHOT_W, SHOT_H   = 278, 156
MAIN_W, MAIN_H   = 720, 405
THUMB_W, THUMB_H = 116, 65


class DetailPage(tk.Frame):
    """Frame halaman detail. Diisi ulang setiap kali game berbeda dibuka."""

    def __init__(self, master, parent_app):
        super().__init__(master, bg=BG_DEEP)
        self.app = parent_app
        self._shot_refs  = []
        self._thumb_refs = []
        self._thumb_cells = []
        self._current_game = None

    def load(self, game: dict):
        """Bersihkan dan render ulang untuk game yang diberikan."""
        for w in self.winfo_children():
            w.destroy()
        self._shot_refs   = []
        self._thumb_refs  = []
        self._thumb_cells = []
        self._current_game = game
        self._build(game)

    # ── Main builder ──────────────────────────────────────────────────────────
    def _build(self, g: dict):
        outer = tk.Frame(self, bg=BG_DEEP)
        outer.pack(fill="both", expand=True)

        # Footer (packed first = pinned bottom)
        tk.Frame(outer, bg=BORDER2, height=1).pack(side="bottom", fill="x")
        foot = tk.Frame(outer, bg=BG_PANEL)
        foot.pack(side="bottom", fill="x")

        tk.Button(foot, text="← Back", font=F(10), fg=TEXT_DIM, bg=BG_SURFACE3,
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  command=self.app._go_back).pack(side="left", padx=12, pady=10)
        if g["rawg_count"]:
            tk.Label(foot, text=f"{g['rawg_count']:,} ratings",
                     font=F(9), fg=TEXT_MUTED, bg=BG_PANEL).pack(side="left", padx=4)

        self._det_wl_var = tk.StringVar()
        self._det_wl_var.set("♥ Remove from Wishlist" if STORE.in_wl(g["slug"]) else "♡ Add to Wishlist")
        tk.Button(foot, textvariable=self._det_wl_var, font=F(10), fg=AMBER, bg=AMBER_BG,
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  command=lambda: self._toggle_wl(g)).pack(side="right", padx=6, pady=10)

        has_price = g.get("is_free") or (g.get("price") not in ("N/A", "", None))
        if has_price:
            steam_url = (f"https://store.steampowered.com/app/{g['steam_appid']}"
                         if g.get("steam_appid") else
                         f"https://store.steampowered.com/search/?term={g['title'].replace(' ', '+')}")
            price_lbl = "FREE" if g.get("is_free") else g["price"]
            tk.Button(foot, text=f"Buy Now   {price_lbl}".strip(),
                      font=F(11, True), fg=TEXT_WHITE, bg=ACCENT, activebackground=ACCENT_LIGHT,
                      relief="flat", cursor="hand2", padx=22, pady=8,
                      command=lambda url=steam_url: webbrowser.open(url)
                      ).pack(side="right", padx=4, pady=10)

        # Tab bar
        tk.Frame(outer, bg=BORDER2, height=1).pack(side="bottom", fill="x")
        tbar = tk.Frame(outer, bg=BG_PANEL)
        tbar.pack(side="bottom", fill="x")
        tk.Frame(outer, bg=BORDER2, height=1).pack(side="bottom", fill="x")

        self._dtab_btns = {}
        self._dtab_frms = {}

        # Tab content area
        self._dtcontent = tk.Frame(outer, bg=BG_DEEP, height=220)
        self._dtcontent.pack(side="bottom", fill="x")
        self._dtcontent.pack_propagate(False)

        for tid, tlabel in [("info",   "  Info & Description  "),
                             ("reqs",   "  PC Requirements  "),
                             ("review", "  ★ My Review  ")]:
            btn = tk.Button(tbar, text=tlabel, font=F(10), fg=TEXT_DIM, bg=BG_PANEL,
                            activebackground=BG_PANEL, activeforeground=TEXT_WHITE,
                            relief="flat", cursor="hand2", pady=11,
                            command=lambda t=tid: self._dtab(t))
            btn.pack(side="left")
            self._dtab_btns[tid] = btn

        self._dtab_frms["info"]   = self._frame_info(g)
        self._dtab_frms["reqs"]   = self._frame_reqs(g)
        self._dtab_frms["review"] = self._frame_review(g)
        self._dtab("info")

        # Top section: screenshot | info panel
        top = tk.Frame(outer, bg=BG_DEEP)
        top.pack(fill="both", expand=True)

        # Right info panel
        info_panel = tk.Frame(top, bg=BG_PANEL, width=290)
        info_panel.pack(side="right", fill="y")
        info_panel.pack_propagate(False)
        tk.Frame(info_panel, bg=BORDER2, width=1).pack(side="left", fill="y")
        ip = tk.Frame(info_panel, bg=BG_PANEL)
        ip.pack(fill="both", expand=True, padx=14, pady=12)

        tk.Label(ip, text=g["title"], font=F(13, True), fg=TEXT_WHITE, bg=BG_PANEL,
                 wraplength=260, justify="left").pack(anchor="w", pady=(0, 8))

        # Cover thumbnail
        cv_thumb = tk.Canvas(ip, width=258, height=145, bg=g["color"], highlightthickness=0)
        cv_thumb.pack(anchor="w", pady=(0, 10))
        cv_thumb.create_text(129, 72, text=g["title"][0], font=F(26, True), fill=TEXT_MUTED)

        def _sc_thumb(img):
            if img:
                cv_thumb._img = img
                cv_thumb.delete("all")
                cv_thumb.create_image(0, 0, anchor="nw", image=img)

        IMG.get(g["cover_url"], size=(258, 145), cb=lambda img: self.after(0, _sc_thumb, img))

        # Description snippet
        desc_snip = (g.get("description") or "")[:180]
        if len(g.get("description") or "") > 180:
            desc_snip += "..."
        if desc_snip:
            tk.Label(ip, text=desc_snip, font=F(9), fg=TEXT_DIM, bg=BG_PANEL,
                     wraplength=258, justify="left").pack(anchor="w", pady=(0, 8))

        divider(ip, pady=(0, 6))

        for label, val, col in [
            ("RECENT REVIEWS:", g.get("review") or "—",  review_color(g.get("review") or "")),
            ("RELEASE DATE:",   g.get("release_date") or "—", TEXT_WHITE),
            ("DEVELOPER:",      (g.get("developer") or "—")[:26], TEXT_WHITE),
            ("PUBLISHER:",      (g.get("publisher") or g.get("developer") or "—")[:26], TEXT_WHITE),
        ]:
            row = tk.Frame(ip, bg=BG_PANEL)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, font=F(8, True), fg=TEXT_DIM, bg=BG_PANEL,
                     anchor="w", width=15).pack(side="left")
            tk.Label(row, text=val, font=F(9), fg=col, bg=BG_PANEL,
                     anchor="w", wraplength=155, justify="left").pack(side="left")

        divider(ip, pady=(6, 6))

        sf2 = tk.Frame(ip, bg=BG_PANEL)
        sf2.pack(anchor="w", pady=(0, 6))
        rb = tk.Frame(sf2, bg=AMBER_BG, highlightthickness=1, highlightbackground="#2a1e06")
        rb.pack(side="left", padx=(0, 6))
        tk.Label(rb, text=f"★  {g['rating']:.2f}", font=FM(11, True),
                 fg=AMBER, bg=AMBER_BG, padx=8, pady=4).pack(side="left")
        tk.Label(rb, text="RAWG", font=F(8), fg=TEXT_DIM, bg=AMBER_BG, padx=3).pack(side="left")
        if g.get("metacritic"):
            mb = tk.Frame(sf2, bg=GREEN_BG, highlightthickness=1, highlightbackground=GREEN_DIM)
            mb.pack(side="left", padx=(0, 6))
            tk.Label(mb, text=str(g["metacritic"]), font=FM(11, True),
                     fg=meta_color(g["metacritic"]), bg=GREEN_BG, padx=8, pady=4).pack(side="left")
            tk.Label(mb, text="MC", font=F(8), fg=TEXT_DIM, bg=GREEN_BG, padx=3).pack(side="left")

        pc_c = FREE_GREEN if g["is_free"] else ACCENT_LIGHT
        pc_b = GREEN_BG   if g["is_free"] else ACCENT_BG
        pc_x = GREEN_DIM  if g["is_free"] else ACCENT_DIM
        pb2 = tk.Frame(ip, bg=pc_b, highlightthickness=1, highlightbackground=pc_x)
        pb2.pack(anchor="w", pady=(0, 6))
        tk.Label(pb2, text=g["price"], font=FM(12, True), fg=pc_c, bg=pc_b, padx=10, pady=4).pack()

        if g.get("tags"):
            divider(ip, pady=(4, 6))
            tk.Label(ip, text="POPULAR TAGS:", font=F(8, True), fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
            wrap = tk.Frame(ip, bg=BG_PANEL)
            wrap.pack(anchor="w", fill="x")
            row_f = tk.Frame(wrap, bg=BG_PANEL)
            row_f.pack(anchor="w")
            for i, tag in enumerate(g["tags"][:8]):
                if i == 4:
                    row_f = tk.Frame(wrap, bg=BG_PANEL)
                    row_f.pack(anchor="w", pady=(3, 0))
                tk.Label(row_f, text=tag, font=F(8), fg=ACCENT_LIGHT, bg=ACCENT_BG,
                         padx=6, pady=3).pack(side="left", padx=(0, 4), pady=1)

        # Left: screenshot viewer
        self._build_screenshot_area(top, g)
        self._dtab("info")

    # ── Screenshot Viewer ─────────────────────────────────────────────────────
    def _build_screenshot_area(self, parent, g: dict):
        shot_area = tk.Frame(parent, bg="#000000")
        shot_area.pack(side="left", fill="both", expand=True)
        shots = g.get("screenshots") or []
        main_cv = tk.Canvas(shot_area, bg="#0a0a0a", highlightthickness=0)
        main_cv.pack(fill="both", expand=True)

        if not shots:
            main_cv.create_text(360, 200, text="No screenshots available.", font=F(11), fill=TEXT_DIM)
            return

        main_cv.create_text(360, 200, text="Loading...", font=F(11), fill=TEXT_MUTED)
        self._main_shot_url = shots[0]
        self._main_shot_idx = 0

        def _load_main(url, idx=0):
            self._main_shot_url = url
            self._main_shot_idx = idx
            for c in self._thumb_cells:
                try: c.configure(highlightbackground=BORDER2)
                except: pass
            if idx < len(self._thumb_cells):
                try: self._thumb_cells[idx].configure(highlightbackground=ACCENT)
                except: pass
            main_cv.delete("all")
            main_cv.create_text(main_cv.winfo_width() // 2 or 360,
                                main_cv.winfo_height() // 2 or 200,
                                text="Loading...", font=F(10), fill=TEXT_MUTED)

            def _show(img):
                if not img: return
                main_cv._main_img = img
                main_cv.delete("all")
                cw = main_cv.winfo_width() or MAIN_W
                ch = main_cv.winfo_height() or MAIN_H
                x = max(0, (cw - img.width()) // 2)
                y = max(0, (ch - img.height()) // 2)
                main_cv.create_image(x, y, anchor="nw", image=img)

            cw = main_cv.winfo_width() or MAIN_W
            ch = main_cv.winfo_height() or MAIN_H
            IMG.get(url, size=(cw, ch), cb=lambda img: self.after(0, _show, img))

        main_cv.bind("<Button-1>",
                     lambda e: self._open_lightbox(self._main_shot_url,
                                                    getattr(main_cv, "_main_img", None)))

        # Thumbnail strip
        strip_bg = tk.Frame(shot_area, bg="#0d0d0d")
        strip_bg.pack(fill="x")
        strip_cv = tk.Canvas(strip_bg, bg="#0d0d0d", highlightthickness=0, height=THUMB_H + 14)
        strip_cv.pack(fill="x", pady=6, padx=6)
        strip_inner = tk.Frame(strip_cv, bg="#0d0d0d")
        strip_cv.create_window((0, 0), window=strip_inner, anchor="nw")
        strip_inner.bind("<Configure>", lambda e: strip_cv.configure(scrollregion=strip_cv.bbox("all")))
        strip_cv.bind("<MouseWheel>", lambda e: strip_cv.xview_scroll(int(-1 * (e.delta / 120)), "units"))

        for idx, url in enumerate(shots):
            cell = tk.Frame(strip_inner, bg=BG_CARD, highlightthickness=2,
                            highlightbackground=ACCENT if idx == 0 else BORDER2,
                            cursor="hand2")
            cell.pack(side="left", padx=3)
            self._thumb_cells.append(cell)

            tc = tk.Canvas(cell, width=THUMB_W, height=THUMB_H, bg=BG_CARD,
                           highlightthickness=0, cursor="hand2")
            tc.pack()
            tc.create_text(THUMB_W // 2, THUMB_H // 2, text="...", font=F(8), fill=TEXT_MUTED)

            def _lt(img, c=tc, cl=cell, i=idx, u=url):
                if img:
                    self._thumb_refs.append(img)
                    c.delete("all")
                    c.create_image(0, 0, anchor="nw", image=img)
                    c.bind("<Button-1>", lambda e, _i=i, _u=u: _load_main(_u, _i))
                    cl.bind("<Button-1>", lambda e, _i=i, _u=u: _load_main(_u, _i))

            IMG.get(url, size=(THUMB_W, THUMB_H), cb=lambda img, fn=_lt: self.after(0, fn, img))

        self.after(120, lambda: _load_main(shots[0], 0))

    def _open_lightbox(self, url: str, img_ref=None):
        lb = tk.Toplevel(self)
        lb.title("Preview")
        lb.configure(bg="#000000")
        lb.geometry("1100x650")
        lb.grab_set()
        lb.bind("<Escape>", lambda e: lb.destroy())

        hdr = tk.Frame(lb, bg="#0a0a0a")
        hdr.pack(fill="x")
        tk.Button(hdr, text="✕  Close", font=F(10), fg=TEXT_DIM, bg="#0a0a0a",
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  command=lb.destroy).pack(side="right")
        tk.Label(hdr, text="Screenshot Preview", font=F(10, True),
                 fg=TEXT_WHITE, bg="#0a0a0a").pack(side="left", padx=16, pady=8)
        tk.Frame(lb, bg=BORDER2, height=1).pack(fill="x")
        cv = tk.Canvas(lb, bg="#000000", highlightthickness=0)
        cv.pack(fill="both", expand=True)

        def _place(event=None):
            cw, ch = cv.winfo_width(), cv.winfo_height()
            if cw < 2 or ch < 2: return
            cv.delete("all")
            try:
                req  = Request(url, headers={"User-Agent": "BitScore/4.0"})
                data = urlopen(req, timeout=10).read()
                pil  = Image.open(BytesIO(data)).convert("RGB")
                pil.thumbnail((cw - 40, ch - 40), Image.LANCZOS)
                lb._lb_img = ImageTk.PhotoImage(pil)
                cv.create_image((cw - pil.width) // 2, (ch - pil.height) // 2,
                                anchor="nw", image=lb._lb_img)
            except Exception:
                cv.create_text(cw // 2, ch // 2, text="Could not load image.",
                               font=F(10), fill=TEXT_DIM)

        if PIL_AVAILABLE:
            cv.after(80, _place)
            cv.bind("<Configure>", lambda e: _place())
        elif img_ref:
            cv.after(80, lambda: cv.create_image(0, 0, anchor="nw", image=img_ref))

    # ── Tab Switching ─────────────────────────────────────────────────────────
    def _dtab(self, tid: str):
        import tkinter.font as tkfont
        for t, btn in self._dtab_btns.items():
            active = (t == tid)
            btn.configure(fg=TEXT_WHITE if active else TEXT_DIM,
                          bg=BG_SURFACE2 if active else BG_PANEL,
                          font=tkfont.Font(family="Segoe UI", size=10,
                                           weight="bold" if active else "normal"))
        for t, frm in self._dtab_frms.items():
            if t == tid: frm.pack(fill="both", expand=True)
            else:        frm.pack_forget()

    def _toggle_wl(self, g):
        STORE.toggle_wl(g["slug"])
        self._det_wl_var.set("♥ Remove from Wishlist" if STORE.in_wl(g["slug"]) else "♡ Add to Wishlist")

    # ── Tab: Info ─────────────────────────────────────────────────────────────
    def _frame_info(self, g):
        frm  = tk.Frame(self._dtcontent, bg=BG_DEEP)
        grid = tk.Frame(frm, bg=BG_DEEP)
        grid.pack(fill="x", padx=16, pady=12)
        for label, val in [("Platform", "  ·  ".join(g["platforms"]) or "N/A"),
                            ("Tags",     "  ·  ".join(g["tags"][:10]))]:
            if not val: continue
            row = tk.Frame(grid, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER2)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=F(9, True), fg=TEXT_DIM, bg=BG_CARD,
                     width=10, anchor="w", padx=12, pady=7).pack(side="left")
            tk.Frame(row, bg=BORDER2, width=1).pack(side="left", fill="y")
            tk.Label(row, text=val, font=F(9), fg=TEXT_WHITE, bg=BG_CARD,
                     wraplength=580, justify="left", padx=12, pady=7).pack(side="left")

        divider(frm, padx=16, pady=(4, 8))
        tk.Label(frm, text="DESCRIPTION", font=F(8, True), fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", padx=16)
        df = tk.Frame(frm, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER2)
        df.pack(fill="x", padx=16, pady=(4, 12))
        vs = ttk.Scrollbar(df, orient="vertical", style="Dark.Vertical.TScrollbar")
        desc_text = g["description"] or "(No description available)"
        approx_lines = max(8, min(20, len(desc_text) // 80 + desc_text.count("\n") + 2))
        dt = tk.Text(df, font=F(10), fg=TEXT_DIM, bg=BG_CARD, relief="flat",
                     wrap="word", yscrollcommand=vs.set, highlightthickness=0,
                     padx=12, pady=8, insertbackground=TEXT_WHITE, height=approx_lines)
        vs.configure(command=dt.yview)
        vs.pack(side="right", fill="y")
        dt.pack(fill="both", expand=True)
        dt.bind("<MouseWheel>", lambda e: dt.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        dt.insert("1.0", desc_text)
        dt.configure(state="disabled")
        return frm

    # ── Tab: PC Requirements ──────────────────────────────────────────────────
    def _frame_reqs(self, g):
        frm = tk.Frame(self._dtcontent, bg=BG_DEEP)
        if not g.get("pc_minimum") and not g.get("pc_recommended"):
            tk.Label(frm, text="PC Requirements data not available.",
                     font=F(10), fg=TEXT_DIM, bg=BG_DEEP).pack(pady=40)
            return frm

        outer = tk.Frame(frm, bg=BG_DEEP)
        outer.pack(fill="both", expand=True)
        req_canvas = tk.Canvas(outer, bg=BG_DEEP, highlightthickness=0)
        req_vsb = ttk.Scrollbar(outer, orient="vertical", command=req_canvas.yview,
                                style="Dark.Vertical.TScrollbar")
        req_canvas.configure(yscrollcommand=req_vsb.set)
        req_vsb.pack(side="right", fill="y")
        req_canvas.pack(side="left", fill="both", expand=True)
        cf = tk.Frame(req_canvas, bg=BG_DEEP)
        req_canvas.create_window((0, 0), window=cf, anchor="nw")
        cf.bind("<Configure>", lambda e: req_canvas.configure(scrollregion=req_canvas.bbox("all")))

        ICON_MAP = {
            "OS": "💻", "PROCESSOR": "⚙️", "CPU": "⚙️",
            "MEMORY": "🧠", "RAM": "🧠",
            "GRAPHICS": "🎮", "GPU": "🎮",
            "DIRECTX": "🔷", "NETWORK": "🌐",
            "STORAGE": "💾", "HARD DRIVE": "💾",
            "SOUND CARD": "🔊", "AUDIO": "🔊",
            "ADDITIONAL NOTES": "📌",
        }

        def _mw(e): req_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def _build_col(parent, sec_title, raw_text, accent_col):
            if not raw_text: return
            parsed = parse_reqs(raw_text)
            if not parsed: return
            sec_hdr = tk.Frame(parent, bg=BG_SURFACE3, highlightthickness=1, highlightbackground=BORDER2)
            sec_hdr.pack(fill="x")
            tk.Frame(sec_hdr, bg=accent_col, width=4).pack(side="left", fill="y")
            tk.Label(sec_hdr, text=sec_title, font=F(11, True), fg=accent_col,
                     bg=BG_SURFACE3, pady=10, padx=14).pack(side="left", anchor="w")
            sec_hdr.bind("<MouseWheel>", _mw)
            card = tk.Frame(parent, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER2)
            card.pack(fill="both", expand=True)
            card.bind("<MouseWheel>", _mw)
            for idx, (key, val) in enumerate(parsed):
                row_bg = BG_CARD if idx % 2 == 0 else BG_SURFACE3
                row = tk.Frame(card, bg=row_bg)
                row.pack(fill="x")
                row.bind("<MouseWheel>", _mw)
                if key:
                    icon = ICON_MAP.get(key, "▸")
                    kl = tk.Label(row, text=f"{icon}  {key}", font=F(9, True), fg=TEXT_DIM,
                                  bg=row_bg, anchor="w", width=16, padx=0, pady=8)
                    kl.pack(side="left")
                    kl.bind("<MouseWheel>", _mw)
                    tk.Frame(row, bg=BORDER2, width=1).pack(side="left", fill="y", pady=6)
                    vl = tk.Label(row, text=val, font=F(9), fg=TEXT_WHITE, bg=row_bg,
                                  anchor="w", padx=10, pady=8, wraplength=220, justify="left")
                    vl.pack(side="left", fill="x", expand=True)
                    vl.bind("<MouseWheel>", _mw)
                else:
                    note = tk.Label(row, text=f"  {val}", font=F(8), fg=TEXT_MUTED, bg=row_bg,
                                    anchor="w", padx=12, pady=5, wraplength=260, justify="left")
                    note.pack(fill="x")
                    note.bind("<MouseWheel>", _mw)

        row_frame = tk.Frame(cf, bg=BG_DEEP)
        row_frame.pack(fill="x", padx=12, pady=12)
        has_min = bool(g.get("pc_minimum"))
        has_rec = bool(g.get("pc_recommended"))
        if has_min and has_rec:
            col_min = tk.Frame(row_frame, bg=BG_DEEP)
            col_min.pack(side="left", fill="both", expand=True, padx=(0, 6))
            tk.Frame(row_frame, bg=BORDER2, width=1).pack(side="left", fill="y", pady=4)
            col_rec = tk.Frame(row_frame, bg=BG_DEEP)
            col_rec.pack(side="left", fill="both", expand=True, padx=(6, 0))
            _build_col(col_min, "Minimum Requirements",    g.get("pc_minimum", ""),     AMBER)
            _build_col(col_rec, "Recommended Requirements", g.get("pc_recommended", ""), ACCENT_LIGHT)
        elif has_min:
            single = tk.Frame(row_frame, bg=BG_DEEP)
            single.pack(fill="x")
            _build_col(single, "Minimum Requirements", g.get("pc_minimum", ""), AMBER)
        else:
            single = tk.Frame(row_frame, bg=BG_DEEP)
            single.pack(fill="x")
            _build_col(single, "Recommended Requirements", g.get("pc_recommended", ""), ACCENT_LIGHT)
        return frm

    # ── Tab: Review ───────────────────────────────────────────────────────────
    def _frame_review(self, g):
        frm = tk.Frame(self._dtcontent, bg=BG_DEEP)
        self._rv_frame = frm
        self._current_review_game = g
        self._render_review_tab()
        return frm

    def _render_review_tab(self):
        frm  = self._rv_frame
        g    = self._current_review_game
        slug = g["slug"]
        for w in frm.winfo_children():
            w.destroy()

        if STORE.has_rv(slug):
            rv = STORE.get_rv(slug)
            card = tk.Frame(frm, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER2)
            card.pack(fill="x", padx=16, pady=(16, 8))
            hd = tk.Frame(card, bg=BG_CARD)
            hd.pack(fill="x", padx=14, pady=(12, 4))
            sf2 = tk.Frame(hd, bg=BG_CARD)
            sf2.pack(side="left")
            for i in range(1, 6):
                tk.Label(sf2, text="★", font=F(18),
                         fg=AMBER if i <= rv["score"] else TEXT_MUTED, bg=BG_CARD).pack(side="left")
            labels = {1: "Poor", 2: "Fair", 3: "Average", 4: "Good", 5: "Outstanding!"}
            tk.Label(hd, text=labels.get(rv["score"], ""), font=F(10, True), fg=AMBER, bg=BG_CARD).pack(side="left", padx=10)
            tk.Label(hd, text=rv.get("date", ""), font=F(9), fg=TEXT_MUTED, bg=BG_CARD).pack(side="right")
            if rv["text"]:
                divider(card, padx=14, pady=0)
                tk.Label(card, text=rv["text"], font=F(10), fg=TEXT_WHITE, bg=BG_CARD,
                         wraplength=680, justify="left", padx=14, pady=10).pack(anchor="w")
            act = tk.Frame(frm, bg=BG_DEEP)
            act.pack(anchor="w", padx=16, pady=(0, 8))
            tk.Button(act, text="Hapus", font=F(10), fg=RED_COL, bg=RED_BG,
                      relief="flat", cursor="hand2", padx=16, pady=7,
                      command=lambda: self._del_review(slug)).pack(side="left")
            divider(frm, padx=16, pady=(0, 4))
            tk.Label(frm, text="EDIT REVIEW", font=F(8, True), fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", padx=16)
        else:
            tk.Label(frm, text="WRITE YOUR REVIEW", font=F(8, True), fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", padx=16, pady=(16, 0))

        existing = STORE.get_rv(slug)
        form = tk.Frame(frm, bg=BG_DEEP)
        form.pack(fill="x", padx=16, pady=(8, 0))
        tk.Label(form, text="RATING", font=F(8, True), fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w")
        star_row = tk.Frame(form, bg=BG_DEEP)
        star_row.pack(anchor="w", pady=(4, 2))
        score_var = tk.IntVar(value=existing["score"] if existing else 0)
        star_btns = []
        star_lbl  = tk.Label(star_row, font=F(9), fg=TEXT_DIM, bg=BG_DEEP)

        def _draw_stars(v):
            for i, b in enumerate(star_btns, 1):
                b.configure(fg=AMBER if i <= v else TEXT_MUTED)
            labels_s = {0: "Pick a star", 1: "Poor", 2: "Fair", 3: "Average", 4: "Good", 5: "Outstanding!"}
            star_lbl.configure(text=labels_s.get(v, ""))

        def _set_star(v):
            score_var.set(v)
            _draw_stars(v)

        for i in range(1, 6):
            b = tk.Button(star_row, text="★", font=F(22), bg=BG_DEEP, relief="flat", cursor="hand2",
                          activebackground=BG_DEEP, activeforeground=AMBER,
                          command=lambda v=i: _set_star(v))
            b.pack(side="left", padx=1)
            b.bind("<Enter>", lambda e, v=i: _draw_stars(v))
            b.bind("<Leave>", lambda e: _draw_stars(score_var.get()))
            star_btns.append(b)
        star_lbl.pack(side="left", padx=(8, 0))
        _draw_stars(score_var.get())

        tk.Label(form, text="NOTES (optional)", font=F(8, True), fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(10, 4))
        import tkinter.messagebox as msgbox
        tf = tk.Frame(form, bg=BG_SURFACE3, highlightthickness=1, highlightbackground=BORDER2, highlightcolor=ACCENT)
        tf.pack(fill="x")
        txt_widget = tk.Text(tf, font=F(10), fg=TEXT_WHITE, bg=BG_SURFACE3, relief="flat",
                             wrap="word", highlightthickness=0, padx=10, pady=8,
                             insertbackground=TEXT_WHITE, height=5)
        txt_widget.pack(fill="x")
        if existing and existing["text"]:
            txt_widget.insert("1.0", existing["text"])

        def _save_inline():
            if not score_var.get():
                msgbox.showerror("Error", "Please select a star rating first!", parent=self)
                return
            STORE.set_rv(slug, score_var.get(), txt_widget.get("1.0", "end").strip())
            self._render_review_tab()

        btn_row = tk.Frame(form, bg=BG_DEEP)
        btn_row.pack(anchor="w", pady=(10, 16))
        tk.Button(btn_row, text="💾  Save Review", font=F(10, True), fg=TEXT_WHITE, bg=ACCENT,
                  activebackground=ACCENT_LIGHT, relief="flat", cursor="hand2",
                  padx=20, pady=8, command=_save_inline).pack(side="left")

    def _del_review(self, slug):
        import tkinter.messagebox as msgbox
        if msgbox.askyesno("Delete", "Delete this review?", parent=self):
            STORE.del_rv(slug)
            self._render_review_tab()
