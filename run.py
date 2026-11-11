"""Dasturni lokal ishga tushirish: python run.py"""
from kirnavbat.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
