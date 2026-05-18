"""
ui/pages/spec_page.py
=====================
Halaman Spec Recommender: input spesifikasi PC dan tampilkan game yang cocok.
"""

import re
import tkinter as tk
import tkinter.ttk as ttk

from config.settings import COVER_W, COVER_H
from config.theme import (
    BG_DEEP, BG_PANEL, BG_CARD, BG_CARD_HVR, BG_SURFACE3,
    BORDER2, ACCENT, ACCENT_LIGHT, ACCENT_BG, ACCENT_DIM,
    GREEN, GREEN_BG, GREEN_DIM, AMBER, AMBER_BG,
    RED_COL, RED_BG, TEAL, TEAL_BG,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED,
    F, FM, divider, meta_color,
)
from utils.img_cache import IMG
from utils.spec_recommender import SpecMatcher

PC_PLATFORM_NAMES = {"PC", "Windows", "macOS", "Linux", "Mac"}

STATUS_STYLE = {
    "smooth":  (GREEN,    GREEN_BG,    GREEN_DIM,  "● Smooth"),
    "maybe":   (AMBER,    AMBER_BG,    "#3a2a06",  "◐ Maybe"),
    "heavy":   (RED_COL,  RED_BG,      "#3a0a08",  "✕ Heavy"),
    "unknown": (TEXT_DIM, BG_SURFACE3, BORDER2,    "? Unknown"),
}

# CPU & GPU autocomplete lists (sorted longest-first for best match)
_CPU_LIST = sorted([
    "i9-13900K","i9-13900","i9-12900K","i9-12900","i9-11900K","i9-11900",
    "i9-10900K","i9-10900","i9-9900K","i9-9900",
    "i7-13700K","i7-13700","i7-12700K","i7-12700","i7-11700K","i7-11700",
    "i7-10700K","i7-10700","i7-9700K","i7-9700","i7-8700K","i7-8700",
    "i7-7700K","i7-7700","i7-6700K","i7-6700",
    "i5-13600K","i5-13600","i5-12600K","i5-12600","i5-11600K","i5-11600",
    "i5-10600K","i5-10600","i5-10400F","i5-10400","i5-9600K","i5-9600",
    "i5-9400F","i5-9400","i5-8600K","i5-8600","i5-8400","i5-7400","i5-6600",
    "i5-4690K","i5-4690","i5-3570K","i5-3570",
    "i3-12100F","i3-12100","i3-10100F","i3-10100","i3-9100F","i3-9100",
    "i3-8100","i3-7100","i3-6100",
    "Ryzen 9 7950X","Ryzen 9 7900X","Ryzen 9 5950X","Ryzen 9 5900X","Ryzen 9 3900X",
    "Ryzen 7 7700X","Ryzen 7 5800X","Ryzen 7 5700X","Ryzen 7 3700X","Ryzen 7 2700X",
    "Ryzen 5 7600X","Ryzen 5 5600X","Ryzen 5 5600","Ryzen 5 3600X","Ryzen 5 3600",
    "Ryzen 5 2600X","Ryzen 5 2600","Ryzen 5 1600",
    "Ryzen 3 4300G","Ryzen 3 3300X","Ryzen 3 3100","Ryzen 3 2200G",
    "Pentium G6600","Pentium G5400","Celeron G5920","Athlon 3000G",
], key=len, reverse=True)

_GPU_LIST = sorted([
    "RTX 4090","RTX 4080","RTX 4070 Ti","RTX 4070","RTX 4060 Ti","RTX 4060",
    "RTX 3090 Ti","RTX 3090","RTX 3080 Ti","RTX 3080","RTX 3070 Ti","RTX 3070",
    "RTX 3060 Ti","RTX 3060","RTX 3050",
    "RTX 2080 Ti","RTX 2080 Super","RTX 2080","RTX 2070 Super","RTX 2070",
    "RTX 2060 Super","RTX 2060",
    "GTX 1080 Ti","GTX 1080","GTX 1070 Ti","GTX 1070","GTX 1060 6GB",
    "GTX 1060 3GB","GTX 1060","GTX 1050 Ti","GTX 1050",
    "GTX 980 Ti","GTX 980","GTX 970","GTX 960","GTX 950",
    "GTX 750 Ti","GTX 750","GT 1030",
    "RX 7900 XTX","RX 7900 XT","RX 6950 XT","RX 6900 XT",
    "RX 6800 XT","RX 6800","RX 6700 XT","RX 6600 XT","RX 6600",
    "RX 5700 XT","RX 5700","RX 5600 XT","RX 5500 XT","RX 5500",
    "RX 590","RX 580 8GB","RX 580","RX 570","RX 480","RX 470","RX 460",
    "R9 390","R9 380","R9 290X","R9 290",
    "Intel Arc A770","Intel Arc A750","Intel Arc A580","Intel Arc A380",
    "Intel UHD 770","Intel UHD 730","Intel UHD 630","Intel UHD 620",
    "Intel Iris Xe","Intel HD 630","Intel HD 620",
    "Vega 56","Vega 64",
], key=len, reverse=True)


class SpecPage(tk.Frame):
    def __init__(self, master, parent_app):
        super().__init__(master, bg=BG_DEEP)
        self.app = parent_app
        self._spec_ram = tk.StringVar()
        self._spec_cpu = tk.StringVar()
        self._spec_gpu = tk.StringVar()
        self._cpu_popup = None
        self._gpu_popup = None
        self._ram_btns  = {}
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_PANEL)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=2).pack(fill="x")
        tk.Label(hdr, text="Game Recommendations Based on PC Specs",
                 font=F(14, True), fg=TEXT_WHITE, bg=BG_PANEL).pack(anchor="w", padx=20, pady=(14, 2))
        tk.Label(hdr, text="Enter your PC/laptop specs and BitScore will match games that can run smoothly.",
                 font=F(9), fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w", padx=20, pady=(0, 14))
        tk.Frame(hdr, bg=BORDER2, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG_DEEP)
        body.pack(fill="both", expand=True)

        # Left: input form
        form_outer = tk.Frame(body, bg=BG_PANEL, width=320)
        form_outer.pack(side="left", fill="y")
        form_outer.pack_propagate(False)
        tk.Frame(form_outer, bg=BORDER2, width=1).pack(side="right", fill="y")
        form = tk.Frame(form_outer, bg=BG_PANEL)
        form.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(form, text="YOUR PC SPECIFICATIONS", font=F(9, True),
                 fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 14))

        # RAM buttons
        tk.Label(form, text="RAM", font=F(9, True), fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w")
        ram_frame = tk.Frame(form, bg=BG_PANEL)
        ram_frame.pack(fill="x", pady=(4, 12))
        for opt in ["4 GB", "6 GB", "8 GB", "16 GB", "32 GB"]:
            val = opt.split()[0]
            btn = tk.Button(ram_frame, text=opt, font=F(9), fg=TEXT_DIM, bg=BG_SURFACE3,
                            relief="flat", cursor="hand2", padx=10, pady=6,
                            command=lambda v=val, o=opt: self._select_ram(v, o))
            btn.pack(side="left", padx=(0, 4))
            self._ram_btns[opt] = btn

        # CPU entry
        tk.Label(form, text="Processor / CPU", font=F(9, True), fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w")
        cpu_ef = tk.Frame(form, bg=BG_SURFACE3, highlightthickness=1,
                          highlightbackground=BORDER2, highlightcolor=ACCENT)
        cpu_ef.pack(fill="x", pady=(4, 2))
        self._cpu_entry = tk.Entry(cpu_ef, textvariable=self._spec_cpu, font=F(10),
                                   fg=TEXT_WHITE, bg=BG_SURFACE3, insertbackground=TEXT_WHITE,
                                   relief="flat", highlightthickness=0)
        self._cpu_entry.pack(fill="x", padx=8, ipady=7)
        tk.Label(form, text="Contoh: i5-10400  atau  Ryzen 5 3600",
                 font=F(8), fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 12))
        self._spec_cpu.trace_add("write", lambda *_: self._ac_update("cpu"))
        self._cpu_entry.bind("<FocusOut>", lambda e: self.after(200, self._ac_close, "cpu"))

        # GPU entry
        tk.Label(form, text="GPU / Kartu Grafis", font=F(9, True), fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w")
        gpu_ef = tk.Frame(form, bg=BG_SURFACE3, highlightthickness=1,
                          highlightbackground=BORDER2, highlightcolor=ACCENT)
        gpu_ef.pack(fill="x", pady=(4, 2))
        self._gpu_entry = tk.Entry(gpu_ef, textvariable=self._spec_gpu, font=F(10),
                                   fg=TEXT_WHITE, bg=BG_SURFACE3, insertbackground=TEXT_WHITE,
                                   relief="flat", highlightthickness=0)
        self._gpu_entry.pack(fill="x", padx=8, ipady=7)
        tk.Label(form, text="Contoh: GTX 1060  atau  RX 580",
                 font=F(8), fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 12))
        self._spec_gpu.trace_add("write", lambda *_: self._ac_update("gpu"))
        self._gpu_entry.bind("<FocusOut>", lambda e: self.after(200, self._ac_close, "gpu"))

        divider(form, pady=(4, 12))

        # Presets
        tk.Label(form, text="COMMON SPEC PRESETS", font=F(8, True), fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 8))
        presets = [
            ("Low-End",  "4",  "i3-7100",  "GTX 750 Ti"),
            ("Mid-End",  "8",  "i5-8400",  "GTX 1060"),
            ("High-End", "16", "i7-10700",  "RTX 3070"),
            ("Ultra",    "32", "i9-12900",  "RTX 4080"),
        ]
        preset_colors = [RED_COL, AMBER, GREEN, TEAL]
        for (name, ram, cpu, gpu), color in zip(presets, preset_colors):
            def _apply(r=ram, c=cpu, g=gpu):
                self._spec_ram.set(r)
                self._spec_cpu.set(c)
                self._spec_gpu.set(g)
                self._select_ram(r, f"{r} GB")
            tk.Button(form, text=name, font=F(9), fg=color, bg=BG_SURFACE3,
                      relief="flat", cursor="hand2", padx=10, pady=5,
                      command=_apply).pack(side="left", padx=(0, 6), pady=(0, 12))

        tk.Button(form, text="Find Matching Games", font=F(11, True),
                  fg=TEXT_WHITE, bg=ACCENT, activebackground=ACCENT_LIGHT,
                  relief="flat", cursor="hand2", padx=0, pady=10,
                  command=self._run_spec_check).pack(fill="x", pady=(8, 0))

        self._spec_info = tk.Label(form, text="", font=F(9), fg=TEXT_DIM,
                                    bg=BG_PANEL, wraplength=270, justify="left")
        self._spec_info.pack(anchor="w", pady=(8, 0))

        # Right: results
        res_area = tk.Frame(body, bg=BG_DEEP)
        res_area.pack(side="left", fill="both", expand=True)

        # Legend bar
        leg = tk.Frame(res_area, bg=BG_PANEL)
        leg.pack(fill="x")
        tk.Frame(leg, bg=BORDER2, height=1).pack(fill="x", side="bottom")
        leg_inner = tk.Frame(leg, bg=BG_PANEL)
        leg_inner.pack(side="left", padx=16, pady=10)
        for txt, color, _ in [("Smooth", GREEN, GREEN_BG), ("Maybe", AMBER, AMBER_BG),
                               ("Heavy", RED_COL, RED_BG), ("Unknown", TEXT_DIM, BG_SURFACE3)]:
            tk.Frame(leg_inner, bg=color, width=10, height=10).pack(side="left", padx=(0, 4))
            tk.Label(leg_inner, text=txt, font=F(9), fg=TEXT_WHITE, bg=BG_PANEL).pack(side="left", padx=(0, 16))
        self._spec_count_lbl = tk.Label(leg, text="", font=F(9), fg=TEXT_MUTED, bg=BG_PANEL)
        self._spec_count_lbl.pack(side="right", padx=16)
        tk.Button(leg, text="🔍 Find Matching Games", font=F(10, True),
                  fg=TEXT_WHITE, bg=ACCENT, activebackground=ACCENT_LIGHT,
                  relief="flat", cursor="hand2", padx=16, pady=6,
                  command=self._run_spec_check).pack(side="right", padx=(0, 8), pady=6)

        # Scrollable results
        rc = tk.Frame(res_area, bg=BG_DEEP)
        rc.pack(fill="both", expand=True)
        self.spec_cvlist = tk.Canvas(rc, bg=BG_DEEP, highlightthickness=0)
        svsb = ttk.Scrollbar(rc, orient="vertical", command=self.spec_cvlist.yview,
                             style="Dark.Vertical.TScrollbar")
        self.spec_cvlist.configure(yscrollcommand=svsb.set)
        svsb.pack(side="right", fill="y")
        self.spec_cvlist.pack(side="left", fill="both", expand=True)
        self.spec_gf = tk.Frame(self.spec_cvlist, bg=BG_DEEP)
        self.spec_cw = self.spec_cvlist.create_window((0, 0), window=self.spec_gf, anchor="nw")
        self.spec_gf.bind("<Configure>", lambda e: self.spec_cvlist.configure(scrollregion=self.spec_cvlist.bbox("all")))
        self.spec_cvlist.bind("<Configure>", lambda e: self.spec_cvlist.itemconfig(self.spec_cw, width=e.width))
        self.spec_cvlist.bind("<MouseWheel>", lambda e: self.spec_cvlist.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.spec_gf.bind("<MouseWheel>",    lambda e: self.spec_cvlist.yview_scroll(int(-1*(e.delta/120)), "units"))

        tk.Label(self.spec_gf,
                 text="Enter your PC specs and click 'Find Matching Games'.\n\nBitScore will compare your specs against PC Requirements\nfor every scraped game.",
                 font=F(11), fg=TEXT_DIM, bg=BG_DEEP, justify="center").pack(pady=80)

    # ── Autocomplete ──────────────────────────────────────────────────────────
    def _ac_update(self, field: str):
        var    = self._spec_cpu if field == "cpu" else self._spec_gpu
        entry  = self._cpu_entry if field == "cpu" else self._gpu_entry
        source = _CPU_LIST if field == "cpu" else _GPU_LIST
        q      = var.get().strip().lower()
        self._ac_close(field)
        if len(q) < 2: return
        matches = [item for item in source if q in item.lower()][:10]
        if not matches: return

        pop = tk.Toplevel(self)
        pop.overrideredirect(True)
        pop.configure(bg=BG_PANEL)
        if field == "cpu": self._cpu_popup = pop
        else:              self._gpu_popup = pop

        tk.Frame(pop, bg=ACCENT, height=2).pack(fill="x")
        ex = entry.winfo_rootx()
        ey = entry.winfo_rooty() + entry.winfo_height() + 2
        ew = entry.master.winfo_width()
        pop.geometry(f"{ew}x{len(matches)*34}+{ex}+{ey}")

        for item in matches:
            row = tk.Frame(pop, bg=BG_PANEL, cursor="hand2")
            row.pack(fill="x")
            lf  = tk.Frame(row, bg=BG_PANEL)
            lf.pack(side="left", padx=8, pady=6)
            idx = item.lower().find(q)
            if idx >= 0:
                if idx > 0:
                    tk.Label(lf, text=item[:idx], font=F(10), fg=TEXT_WHITE, bg=BG_PANEL).pack(side="left")
                tk.Label(lf, text=item[idx:idx+len(q)], font=F(10, True), fg=ACCENT_LIGHT, bg=BG_PANEL).pack(side="left")
                rest = item[idx+len(q):]
                if rest: tk.Label(lf, text=rest, font=F(10), fg=TEXT_WHITE, bg=BG_PANEL).pack(side="left")
            else:
                tk.Label(lf, text=item, font=F(10), fg=TEXT_WHITE, bg=BG_PANEL).pack(side="left")
            tk.Frame(pop, bg=BORDER2, height=1).pack(fill="x")

            def _pick(v=item, f=field):
                if f == "cpu": self._spec_cpu.set(v)
                else:          self._spec_gpu.set(v)
                self._ac_close(f)

            row.bind("<Button-1>", lambda e, fn=_pick: fn())
            for w in lf.winfo_children():
                w.bind("<Button-1>", lambda e, fn=_pick: fn())
            row.bind("<Enter>", lambda e, r=row: r.configure(bg=BG_SURFACE3))
            row.bind("<Leave>", lambda e, r=row: r.configure(bg=BG_PANEL))

    def _ac_close(self, field: str):
        if field == "cpu" and self._cpu_popup:
            try: self._cpu_popup.destroy()
            except: pass
            self._cpu_popup = None
        elif field == "gpu" and self._gpu_popup:
            try: self._gpu_popup.destroy()
            except: pass
            self._gpu_popup = None

    def _select_ram(self, val: str, opt: str):
        self._spec_ram.set(val)
        for o, btn in self._ram_btns.items():
            if f"{val} GB" == o or o == opt:
                btn.configure(fg=TEXT_WHITE, bg=ACCENT)
            else:
                btn.configure(fg=TEXT_DIM, bg=BG_SURFACE3)

    # ── Run check ─────────────────────────────────────────────────────────────
    def _run_spec_check(self):
        ram_str = self._spec_ram.get().strip()
        cpu_str = self._spec_cpu.get().strip()
        gpu_str = self._spec_gpu.get().strip()

        if not ram_str and not cpu_str and not gpu_str:
            self._spec_info.configure(text="Masukkan minimal RAM, CPU, atau GPU.", fg=RED_COL)
            return

        try:
            user_ram = int(re.sub(r"[^0-9]", "", ram_str)) if ram_str else 8
        except Exception:
            user_ram = 8

        user_cpu = SpecMatcher.user_cpu_tier(cpu_str) if cpu_str else 5
        user_gpu = SpecMatcher.user_gpu_tier(gpu_str) if gpu_str else 5

        self._spec_info.configure(
            text=f"RAM: {user_ram}GB  |  CPU tier: {user_cpu}/10  |  GPU tier: {user_gpu}/10",
            fg=TEAL)

        if not self.app.games:
            self._spec_info.configure(text="No game data yet. Scrape from the main page first!", fg=RED_COL)
            return

        results = []
        for g in self.app.games:
            platforms = set(g.get("platforms") or [])
            if not platforms.intersection(PC_PLATFORM_NAMES):
                continue
            status = SpecMatcher.check_game(g, user_ram, user_cpu, user_gpu)
            results.append((g, status))

        order = {"smooth": 0, "maybe": 1, "heavy": 2, "unknown": 3}
        results.sort(key=lambda x: (order.get(x[1], 3), -x[0]["rating"]))
        self._render_results(results)

    # ── Render results ────────────────────────────────────────────────────────
    def _render_results(self, results):
        for w in self.spec_gf.winfo_children():
            w.destroy()

        counts = {"smooth": 0, "maybe": 0, "heavy": 0, "unknown": 0}
        for _, s in results:
            counts[s] = counts.get(s, 0) + 1
        self._spec_count_lbl.configure(
            text=f"Smooth: {counts['smooth']}  ·  Maybe: {counts['maybe']}  ·  Heavy: {counts['heavy']}  of {len(results)} games")

        for game, status in results:
            sc, sbg, sborder, slabel = STATUS_STYLE.get(status, STATUS_STYLE["unknown"])
            outer = tk.Frame(self.spec_gf, bg=sborder)
            outer.pack(fill="x", pady=2, padx=12)
            card = tk.Frame(outer, bg=BG_CARD, cursor="hand2")
            card.pack(fill="x", padx=1, pady=1)

            def hover_on(e, c=card):  c.configure(bg=BG_CARD_HVR)
            def hover_off(e, c=card): c.configure(bg=BG_CARD)
            card.bind("<Enter>", hover_on)
            card.bind("<Leave>", hover_off)
            card.bind("<Button-1>", lambda e, g=game: self.app._open_detail(g))

            tk.Frame(card, bg=sc, width=5).pack(side="left", fill="y")

            cv = tk.Canvas(card, width=COVER_W, height=COVER_H, bg=game["color"], highlightthickness=0)
            cv.pack(side="left", padx=(4, 10), pady=10)
            cv.create_text(COVER_W // 2, COVER_H // 2, text=game["title"][0], font=F(18, True), fill=TEXT_MUTED)

            def _sc(img, c=cv):
                if img: c._img = img; c.create_image(0, 0, anchor="nw", image=img)

            IMG.get(game["cover_url"], size=(COVER_W, COVER_H),
                    cb=lambda img, fn=_sc: self.after(0, fn, img))

            inf = tk.Frame(card, bg=BG_CARD)
            inf.pack(side="left", fill="both", expand=True, pady=10)
            tk.Label(inf, text=game["title"], font=F(12, True), fg=TEXT_WHITE, bg=BG_CARD, anchor="w").pack(fill="x")

            if game["genres"]:
                gr = tk.Frame(inf, bg=BG_CARD)
                gr.pack(anchor="w", pady=(2, 0))
                for g2 in game["genres"][:3]:
                    tk.Label(gr, text=g2, font=F(8), fg=ACCENT_LIGHT, bg=ACCENT_BG,
                             padx=5, pady=2).pack(side="left", padx=(0, 3))

            rr = tk.Frame(inf, bg=BG_CARD)
            rr.pack(anchor="w", pady=(5, 0))
            rb = tk.Frame(rr, bg=AMBER_BG)
            rb.pack(side="left", padx=(0, 6))
            tk.Label(rb, text=f"★ {game['rating']:.2f}", font=FM(10, True), fg=AMBER, bg=AMBER_BG, padx=7, pady=3).pack()
            if game.get("metacritic"):
                mb = tk.Frame(rr, bg=GREEN_BG)
                mb.pack(side="left", padx=(0, 6))
                tk.Label(mb, text=f"MC {game['metacritic']}", font=FM(9, True),
                         fg=meta_color(game["metacritic"]), bg=GREEN_BG, padx=6, pady=3).pack()

            req_txt = game.get("pc_minimum") or ""
            if req_txt:
                snippet = req_txt[:80] + ("..." if len(req_txt) > 80 else "")
                tk.Label(inf, text=f"Min: {snippet}", font=F(8), fg=TEXT_MUTED,
                         bg=BG_CARD, wraplength=500, justify="left").pack(anchor="w", pady=(3, 0))

            rc2 = tk.Frame(card, bg=BG_CARD)
            rc2.pack(side="right", padx=14, pady=10, anchor="center")
            badge = tk.Frame(rc2, bg=sbg, highlightthickness=1, highlightbackground=sborder)
            badge.pack()
            tk.Label(badge, text=slabel, font=F(10, True), fg=sc, bg=sbg, padx=12, pady=6).pack()
