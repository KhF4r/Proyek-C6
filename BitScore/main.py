"""
BitScore — Game Rating App v4.0
================================
Entry point aplikasi. Jalankan file ini untuk memulai.

Install:
    pip install pillow requests python-dotenv

Jalankan:
    python main.py
"""

from auth.login_page import LoginPage
from UI.app import BitScoreApp

if __name__ == "__main__":
    # 1. Tampilkan halaman login
    login = LoginPage()
    login.mainloop()

    # 2. Jika login berhasil, buka app utama
    if login.success:
        app = BitScoreApp()
        app.mainloop()
