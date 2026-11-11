# KirNavbat — TTJ kir yuvish mashinalariga onlayn navbat

Talabalar turar joyidagi (TTJ) kir yuvish mashinalariga soatbay navbat olish
uchun kichik veb-dastur. «Dasturiy injiniringga kirish» (ISE003) fanidan
mustaqil ish loyihasi.

## Ishga tushirish

```bash
python -m venv venv
venv\Scripts\activate        # Windows  (Linux: source venv/bin/activate)
pip install -r requirements.txt
python run.py                # http://127.0.0.1:5000
```

Birinchi ishga tushishda baza (`instance/kirnavbat.db`) va 4 ta mashina
avtomatik yaratiladi. Demo administrator: `admin` / `admin123`
(birinchi kirishdan keyin parolni almashtiring).

## Testlar

```bash
python -m pytest -v
```

## Papka tuzilishi

```
kirnavbat/
  app.py          # Ekran qatlami: Flask marshrutlari (routes)
  services.py     # Mantiq qatlami: navbat qoidalari, autentifikatsiya
  observer.py     # Observer pattern: hodisa -> xabarnoma
  repository.py   # Ma'lumotlar qatlami: SQLite so'rovlari
  validators.py   # Chegaraviy qiymatlarni tekshirish
  models.py       # Sinflar (dataclass)
  db.py           # Baza sxemasi va ulanish
  templates/      # HTML ekranlar
  static/         # CSS
tests/            # pytest avtomatik testlari
docs/             # Kod qoidalari, o'zgarishlar jurnali
```
