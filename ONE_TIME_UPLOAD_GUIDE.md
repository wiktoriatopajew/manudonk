# 🎯 System Jednorazowego Uploadu - Przewodnik

## ✅ Jak to działa?

**Główna idea:** 
- PDF uploadowany na Google Drive **tylko raz**
- Link zapisany w bazie danych
- Przy kolejnych zakupach → **ten sam link wysyłany automatycznie**

---

## 🚀 Szybki Start (5 kroków)

### KROK 1: Zaktualizuj bazę danych
```powershell
python migrate_db.py
```
✅ Dodaje kolumny: `google_drive_link`, `preview_images`, `pdf_processed`

### KROK 2: Zainstaluj biblioteki
```powershell
pip install -r requirements.txt
```

### KROK 3: Przetwórz produkty
```powershell
# Test
python process_pdfs.py test

# Wszystkie
python process_pdfs.py full
```

### KROK 4: Zaktualizuj bazę  
```powershell
python update_database.py
```

### KROK 5: Gotowe! 🎉
Teraz każdy zakup automatycznie wysyła link Google Drive!

---

## 💰 Co się dzieje po zakupie?

1. Klient płaci przez Stripe ✅
2. Webhook `/api/orders/webhook` wywołany 🔔
3. System sprawdza: `product.google_drive_link` istnieje? 
   - **TAK** → Email z linkiem wysyłany natychmiast 📧
   - **NIE** → Tylko potwierdzenie zamówienia (musisz przetworzyć PDF)

---

## 📁 Potrzebne pliki

### Do testowania lokalnie (bez Google Drive):
- ✅ `pdf_manager.py` - pobieranie i podgląd
- ✅ `migrate_db.py` - aktualizacja bazy
- ✅ `update_database.py` - zapisywanie linków

### Dla pełnej funkcjonalności:
- ✅ `google_drive_manager.py` - upload
- ✅ `process_pdfs.py` - orchestrator
- ✅ `google_drive_credentials.json` - klucze API

---

## 🔍 Sprawdzanie statusu

```python
from database.models import Product, get_session

session = get_session()

# Ile produktów ma linki?
with_links = session.query(Product).filter(
    Product.google_drive_link.isnot(None)
).count()

print(f"✅ Przetworzonych: {with_links}")
```

---

## 📖 Więcej informacji

- **Pełna dokumentacja:** [PDF_SYSTEM_GUIDE.md](PDF_SYSTEM_GUIDE.md)
- **Google Drive setup:** [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md)  
- **Poppler (podgląd):** [POPPLER_SETUP.md](POPPLER_SETUP.md)
