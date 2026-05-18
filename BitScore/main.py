"""
BitScore — Game Rating App v4.0
================================
Entry point aplikasi. Jalankan file ini untuk memulai.

Install:
    pip install pillow requests python-dotenv

Jalankan:
    python main.py
"""

from ui.app import BitScoreApp

if __name__ == "__main__":
    app = BitScoreApp()
    app.mainloop()
