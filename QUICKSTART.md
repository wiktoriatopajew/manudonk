# ⚡ Quick Start - Szybki start

Przewodnik krok po kroku do uruchomienia sklepu w 5 minut.

## 📦 Krok 1: Instalacja (1 min)

```powershell
# Zainstaluj zależności
pip install -r requirements.txt
```

## 📄 Krok 2: Przygotuj dane (1 min)

1. Utwórz plik `products.csv` w głównym katalogu
2. Skopiuj format z `products_example.csv`
3. Dodaj swoje produkty

**Minimalna zawartość (dla testu):**
```csv
title,description,price,category,brand,model
"Test Manual","Test description",9.99,Test,TestBrand,TestModel
```

## 🗄️ Krok 3: Import danych (1 min)

```powershell
# Zaimportuj produkty do bazy
python import_csv.py
```

To automatycznie:
- Utworzy bazę SQLite
- Zaimportuje produkty
- Wygeneruje SEO slugi
- Utworzy indeksy

## 💳 Krok 4: Konfiguracja PayPal (30 sek)

```powershell
# Ustaw PayPal Client ID
$env:PAYPAL_CLIENT_ID="YOUR_PAYPAL_CLIENT_ID"

# LUB użyj testowego (dla rozwoju)
$env:PAYPAL_CLIENT_ID="sandbox_client_id"
```

## 🚀 Krok 5: Uruchom! (30 sek)

```powershell
# Start aplikacji
python main.py
```

Otwórz przeglądarkę: **http://localhost:8000**

---

## ✅ Weryfikacja

### 1. Sprawdź stronę główną
```
http://localhost:8000/
```
✅ Powinna wyświetlać najnowsze produkty

### 2. Sprawdź wyszukiwanie
```
http://localhost:8000/search
```
✅ Filtry powinny działać

### 3. Sprawdź clean URL produktu
```
http://localhost:8000/instrukcje/testbrand-testmodel-testmanual-1
```
✅ Strona produktu powinna się załadować

### 4. Sprawdź SEO
```
http://localhost:8000/robots.txt
http://localhost:8000/sitemap.xml
```
✅ Oba powinny się wyświetlać

---

## 🔧 Opcjonalne: Migracja istniejącej bazy

Jeśli masz już bazę bez slugów:

```powershell
python generate_slugs.py
```

---

## 🐛 Problemy?

### Błąd: "No module named 'fastapi'"
```powershell
pip install -r requirements.txt
```

### Błąd: "File not found: products.csv"
Utwórz plik `products.csv` w głównym katalogu projektu.

### Brak produktów na stronie
1. Sprawdź czy import się powiódł
2. Sprawdź `database/products.db` czy istnieje
3. Uruchom ponownie import

### Clean URLs nie działają (404)
```powershell
python generate_slugs.py
```

---

## 📊 Następne kroki

1. **Dodaj więcej produktów** do pliku CSV
2. **Skonfiguruj prawdziwe PayPal** credentials
3. **Zmień domenę** w `sitemap.xml` i `robots.txt` (zamień `https://strona.pl`)
4. **Dostosuj style** - edytuj templates
5. **Dodaj logo** - umieść w folderze `static/`
6. **Deploy na serwer** - zobacz sekcję deployment w README

---

## 🎉 Gotowe!

Twój sklep jest gotowy! 

Teraz możesz:
- Przesłać sitemap do Google Search Console
- Rozpocząć dodawanie produktów
- Dostosować wygląd
- Skonfigurować automatyczną wysyłkę emaili

---

**Potrzebujesz pomocy? Zobacz:** 
- [README.md](README.md) - Pełna dokumentacja
- [SEO_GUIDE.md](SEO_GUIDE.md) - Przewodnik SEO
- [CHANGELOG.md](CHANGELOG.md) - Co nowego

**Miłego sprzedawania! 💰**
