# 📚 Kompletny Przewodnik - System Automatycznego Pobierania i Dostarczania PDF

## 🎯 Co robi ten system?

System automatycznie:
1. ✅ Pobiera PDF z linków w CSV
2. ✅ Generuje podgląd (pierwsze 5 stron jako obrazy)
3. ✅ Uploaduje na Google Drive
4. ✅ Wysyła link do klienta po zakupie

## 🚀 Szybki Start (Krok po kroku)

### KROK 1: Instalacja wymaganych bibliotek

```powershell
# Aktywuj środowisko wirtualne
.\.venv\Scripts\Activate.ps1

# Zainstaluj biblioteki
pip install -r requirements.txt
```

### KROK 2: Instalacja Poppler (dla generowania podglądu)

1. Pobierz: https://github.com/oschwartz10612/poppler-windows/releases/
2. Rozpakuj do `C:\poppler`
3. Dodaj do PATH: `C:\poppler\Library\bin`
4. Zrestartuj terminal

📝 Szczegóły: Zobacz `POPPLER_SETUP.md`

### KROK 3: Konfiguracja Google Drive (opcjonalne ale zalecane)

1. Przejdź: https://console.cloud.google.com/
2. Utwórz projekt
3. Włącz Google Drive API
4. Utwórz Service Account
5. Pobierz klucz JSON jako `google_drive_credentials.json`

📝 Szczegóły: Zobacz `GOOGLE_DRIVE_SETUP.md`

### KROK 4: Przygotuj CSV z produktami

Format CSV:
```csv
ID,Category,English Title,Original HTML Name,Link PDF
185871,Trucks,Ford F-150 Manual,Ford F-150 Manual,https://example.com/pdf/file.pdf
```

Zapisz jako np. `products.csv`

### KROK 5: Uruchom przetwarzanie

```powershell
# Test z pierwszym produktem
python process_pdfs.py test

# Przetwórz wszystkie produkty
python process_pdfs.py full

# Lub z własnym plikiem CSV
python process_pdfs.py full mojeprodukty.csv
```

### KROK 6: Zaktualizuj bazę danych

```powershell
# Sprawdź co zostanie zmienione (dry run)
python update_database.py --dry-run

# Zastosuj zmiany
python update_database.py
```

### KROK 7: Gotowe! 🎉

Teraz:
- ✅ PDF są zapisane lokalnie w `storage/pdfs/`
- ✅ Podglądy w `static/images/previews/{product_id}/`
- ✅ Linki Google Drive w bazie danych
- ✅ Automatyczna dostawa po zakupie

## 📂 Struktura Plików

```
Strona Manuals/
├── process_pdfs.py              # Główny skrypt orchestrator
├── pdf_manager.py               # Pobieranie i generowanie podglądu
├── google_drive_manager.py      # Upload na Drive
├── update_database.py           # Aktualizacja bazy danych
├── google_drive_credentials.json # Klucze API (dodaj sam!)
├── test2.csv                    # Przykładowe dane
│
├── storage/
│   └── pdfs/                    # Pobrane PDF
│       ├── 185871_Ford_F150.pdf
│       └── ...
│
├── static/
│   └── images/
│       └── previews/            # Podglądy produktów
│           ├── 185871/
│           │   ├── page_1.jpg
│           │   ├── page_2.jpg
│           │   └── ...
│           └── ...
│
└── complete_results.json        # Wyniki przetwarzania
```

## 🔄 Przepływ Pracy

### Dodawanie nowych produktów:

1. Dodaj produkt do CSV (lub bazy danych)
2. Uruchom: `python process_pdfs.py full`
3. Uruchom: `python update_database.py`
4. Gotowe!

### Po zakupie produktu:

System automatycznie:
1. Stripe przetwarza płatność
2. Email wysyłany z linkiem Google Drive
3. Klient pobiera PDF
4. Wszystko działa bez Twojego udziału!

## 🎨 Wyświetlanie Podglądu na Stronie

Podglądy są automatycznie dostępne na stronie produktu.

Zdjęcia znajdują się w:
```
/static/images/previews/{product_id}/page_1.jpg
/static/images/previews/{product_id}/page_2.jpg
...
```

## 💡 Wskazówki i Triki

### Bez Google Drive?

Możesz używać tylko lokalnych plików:
- PDFy w `storage/pdfs/`
- Wysyłaj jako załącznik email (dla małych plików <25MB)
- Lub postaw lokalny serwer plików

### Duże pliki CSV?

Przetwarzaj partiami:
```python
# Edytuj process_pdfs.py, dodaj limit
query = session.query(Product).limit(50).all()
```

### Monitoring

Sprawdź logi w:
- `complete_results.json` - wszystkie wyniki
- `google_drive_upload_results.json` - statusy uploadów

## 🔒 Bezpieczeństwo

⚠️ **WAŻNE**:

```gitignore
# Dodaj do .gitignore:
google_drive_credentials.json
storage/pdfs/
*.json
```

**NIE COMMITUJ**:
- Kluczy API
- Pobranych PDF
- Wyników z danymi osobowymi

## ❓ Rozwiązywanie Problemów

### "poppler not found"
➡️ Zobacz `POPPLER_SETUP.md`

### "Google Drive authentication failed"
➡️ Zobacz `GOOGLE_DRIVE_SETUP.md`

### "File not found in database"
➡️ Sprawdź czy product ID w CSV zgadza się z bazą

### PDF nie pobiera się
➡️ Sprawdź link - czy jest bezpośredni download?
➡️ Niektóre strony wymagają logowania/ciasteczek

## 📞 Potrzebujesz pomocy?

1. Sprawdź README pliki: `*_SETUP.md`
2. Przejrzyj kod - jest dobrze skomentowany
3. Uruchom `--dry-run` przed właściwym przetwarzaniem

## 🎯 Następne Kroki

Po skonfigurowaniu systemu:

1. ✅ Test z jednym produktem
2. ✅ Sprawdź podgląd na stronie
3. ✅ Przetestuj zakup
4. ✅ Sprawdź email z linkiem
5. ✅ Pobierz PDF z Google Drive
6. ✅ Przetwórz wszystkie produkty!

---

## 📋 Checklist Kompletnej Konfiguracji

- [ ] Zainstalowane biblioteki (`pip install -r requirements.txt`)
- [ ] Poppler zainstalowany i w PATH
- [ ] Google Drive API skonfigurowane
- [ ] `google_drive_credentials.json` w folderze projektu
- [ ] CSV z produktami przygotowany
- [ ] Test z pierwszym produktem przeszedł
- [ ] Baza danych zaktualizowana
- [ ] Podgląd widoczny na stronie
- [ ] Test zakupu - email z linkiem działa
- [ ] Gotowe do produkcji! 🚀
