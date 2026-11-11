# Kod yozish qoidalari (KirNavbat)

1. **Nomlash.** O'zgaruvchi va funksiyalar `snake_case`, sinflar `PascalCase`,
   konstantalar `KATTA_HARF` (masalan `MAX_ACTIVE_BOOKINGS`). Nom nima
   qilishini aytsin: `can_cancel`, `book_slot`, `x1` emas.
2. **Izohlar o'zbek tilida (lotin).** Har bir modul va ochiq funksiya
   boshida qisqa docstring: nima qiladi, nima qaytaradi.
3. **Qatlamlar aralashmasin.** `app.py` SQL yozmaydi, `repository.py`
   biznes qoidasini bilmaydi. Qoida faqat `services.py` da.
4. **SQL faqat parametrli.** `?` belgisi bilan; satrni `+` yoki f-string
   bilan SQL ga qo'shish taqiqlanadi (SQL injection).
5. **Sehrli sonlar yo'q.** 8, 22, 2 kabi qiymatlar `validators.py`
   dagi konstantalarda turadi.
6. **Har bir kichik ish — alohida commit.** Xabar shakli:
   `tur: qisqa tavsif` (tur: `feat`, `fix`, `test`, `docs`, `security`,
   `refactor`). Testlar o'tmasa commit qilinmaydi.
