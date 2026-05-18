"""
ui/components/dialogs.py
========================
Dialog popup: ScrapeDialog dan ReviewDialog.
"""

import tkinter as tk
import tkinter.messagebox as msgbox

from config.settings import MAX_SCRAPE
from config.theme import (
    BG_PANEL, BG_SURFACE3, BORDER2,
    ACCENT, ACCENT_LIGHT, AMBER, AMBER_BG,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED,
    F, divider,
)
from store.local_store import STORE


# ──────────────────────────────────────────────────────────────────────────────
#  REVIEW DIALOG
# ──────────────────────────────────────────────────────────────────────────────
class ReviewDialog(tk.Toplevel):
    def __init__(self, parent, game: dict, refresh_cb):
        super().__init__(parent)
        self.game = game
        self.refresh_cb = refresh_cb
        self.title("Write a Review")
        self.configure(bg=BG_PANEL)
        self.geometry("500x440")
        self.resizable(False, False)
        self.grab_set()

        existing = STORE.get_rv(game["slug"])

        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(self, text="Write a Review", font=F(14, True),
                 fg=TEXT_WHITE, bg=BG_PANEL).pack(pady=(18, 2))
        tk.Label(self, text=game["title"], font=F(10),
                 fg=TEXT_DIM, bg=BG_PANEL).pack()
        divider(self, padx=20, pady=12)

        tk.Label(self, text="YOUR RATING", font=F(8, True),
                 fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", padx=24)
        self.score = tk.IntVar(value=existing["score"])
        sf = tk.Frame(self, bg=BG_PANEL)
        sf.pack(anchor="w", padx=24, pady=(6, 14))
        self._stars = []
        for i in range(1, 6):
            btn = tk.Button(sf, text="★", font=F(22), bg=BG_PANEL, relief="flat", cursor="hand2",
                            activebackground=BG_PANEL, activeforeground=AMBER,
                            command=lambda v=i: self._set(v))
            btn.pack(side="left", padx=1)
            self._stars.append(btn)
        for i, btn in enumerate(self._stars, 1):
            btn.bind("<Enter>", lambda e, v=i: self._draw(v))
            btn.bind("<Leave>", lambda e: self._draw(self.score.get()))
        self.score_lbl = tk.Label(sf, font=F(9), fg=TEXT_DIM, bg=BG_PANEL)
        self.score_lbl.pack(side="left", padx=8)
        self._draw(existing["score"])
        self._update_lbl(existing["score"])

        tk.Label(self, text="NOTES (optional)", font=F(8, True),
                 fg=TEXT_MUTED, bg=BG_PANEL, anchor="w").pack(fill="x", padx=24)
        tf = tk.Frame(self, bg=BG_SURFACE3, highlightthickness=1,
                      highlightbackground=BORDER2, highlightcolor=ACCENT)
        tf.pack(fill="both", expand=True, padx=24, pady=(6, 0))
        self.txt = tk.Text(tf, font=F(10), fg=TEXT_WHITE, bg=BG_SURFACE3, relief="flat",
                           wrap="word", highlightthickness=0, padx=10, pady=8,
                           insertbackground=TEXT_WHITE)
        self.txt.pack(fill="both", expand=True)
        if existing["text"]:
            self.txt.insert("1.0", existing["text"])

        divider(self, padx=20, pady=12)
        row = tk.Frame(self, bg=BG_PANEL)
        row.pack(pady=(0, 16))
        tk.Button(row, text="Cancel", font=F(10), fg=TEXT_DIM, bg=BG_SURFACE3,
                  relief="flat", cursor="hand2", padx=20, pady=8,
                  command=self.destroy).pack(side="left", padx=6)
        tk.Button(row, text="Save", font=F(10, True), fg=TEXT_WHITE, bg=ACCENT,
                  activebackground=ACCENT_LIGHT, relief="flat", cursor="hand2",
                  padx=22, pady=8, command=self._save).pack(side="left", padx=6)

    def _set(self, v):
        self.score.set(v)
        self._draw(v)
        self._update_lbl(v)

    def _draw(self, v):
        for i, btn in enumerate(self._stars, 1):
            btn.configure(fg=AMBER if i <= v else TEXT_MUTED)

    def _update_lbl(self, v):
        labels = {0: "Pick a star", 1: "Poor", 2: "Fair", 3: "Average", 4: "Good", 5: "Outstanding!"}
        self.score_lbl.configure(text=labels.get(v, ""))

    def _save(self):
        if not self.score.get():
            msgbox.showerror("Error", "Please select a star rating first!", parent=self)
            return
        STORE.set_rv(self.game["slug"], self.score.get(), self.txt.get("1.0", "end").strip())
        self.refresh_cb()
        self.destroy()


# ──────────────────────────────────────────────────────────────────────────────
#  SCRAPE DIALOG
# ──────────────────────────────────────────────────────────────────────────────
class ScrapeDialog(tk.Toplevel):
    def __init__(self, parent, on_done):
        super().__init__(parent)
        self.on_done = on_done
        self.title("Scrape Games")
        self.configure(bg=BG_PANEL)
        self.geometry("460x320")
        self.resizable(False, False)
        self.grab_set()

        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(self, text="Scraping Configuration", font=F(13, True),
                 fg=TEXT_WHITE, bg=BG_PANEL).pack(pady=(18, 2))
        tk.Label(self, text="RAWG + Steam + CheapShark", font=F(9),
                 fg=TEXT_DIM, bg=BG_PANEL).pack()
        divider(self, padx=20, pady=12)

        tk.Label(self, text="MODE", font=F(8, True), fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", padx=24)
        self.mode = tk.StringVar(value="top")
        for txt, val in [("Top Games by rating", "top"), ("Search by keyword", "search")]:
            tk.Radiobutton(self, text=txt, variable=self.mode, value=val, font=F(10),
                           fg=TEXT_WHITE, bg=BG_PANEL, selectcolor=ACCENT,
                           activebackground=BG_PANEL,
                           command=self._on_mode).pack(anchor="w", padx=24, pady=3)

        inp = tk.Frame(self, bg=BG_PANEL)
        inp.pack(fill="x", padx=24, pady=12)
        self.inp_lbl = tk.Label(inp, text=f"NUMBER OF GAMES (max {MAX_SCRAPE})",
                                font=F(8, True), fg=TEXT_MUTED, bg=BG_PANEL)
        self.inp_lbl.pack(anchor="w", pady=(0, 4))
        self.inp_var = tk.StringVar(value="25")
        tk.Entry(inp, textvariable=self.inp_var, font=F(11), fg=TEXT_WHITE, bg=BG_SURFACE3,
                 insertbackground=TEXT_WHITE, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER2, highlightcolor=ACCENT).pack(fill="x", ipady=7)

        divider(self, padx=20)
        row = tk.Frame(self, bg=BG_PANEL)
        row.pack(pady=10)
        tk.Button(row, text="Cancel", font=F(10), fg=TEXT_DIM, bg=BG_SURFACE3,
                  relief="flat", cursor="hand2", padx=20, pady=8,
                  command=self.destroy).pack(side="left", padx=6)
        tk.Button(row, text="Start Scraping", font=F(10, True), fg=TEXT_WHITE, bg=ACCENT,
                  activebackground=ACCENT_LIGHT, relief="flat", cursor="hand2",
                  padx=22, pady=8, command=self._start).pack(side="left", padx=6)

    def _on_mode(self):
        if self.mode.get() == "top":
            self.inp_lbl.configure(text=f"NUMBER OF GAMES (max {MAX_SCRAPE})")
            self.inp_var.set("25")
        else:
            self.inp_lbl.configure(text="KEYWORD")
            self.inp_var.set("")

    def _start(self):
        v = self.inp_var.get().strip()
        if not v:
            msgbox.showerror("Error", "Input cannot be empty!", parent=self)
            return
        if self.mode.get() == "top" and v.isdigit() and int(v) > MAX_SCRAPE:
            msgbox.showerror("Error", f"Maximum {MAX_SCRAPE} games.", parent=self)
            return
        self.destroy()
        self.on_done(self.mode.get(), v)
