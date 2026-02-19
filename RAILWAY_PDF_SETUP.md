# 🚀 Railway PDF System - Automatyczne Pobieranie i Dostawa przez Google Drive

## 📋 Jak to działa na Railway

1. **Import produktów** → produkty mają wypełnione pole `pdf_url` (link do pobrania PDF)
2. **Przetwarzanie PDF** → skrypt pobiera PDF z `pdf_url` i uploaduje na Google Drive
3. **Aktualizacja bazy** → pole `google_drive_link` zapisuje link do Google Drive
4. **Po zakupie** → email automatycznie wysyła link Google Drive do klienta

## ⚙️ Konfiguracja Railway

### KROK 1: Dodaj Google Drive Service Account

1. Przejdź do: https://console.cloud.google.com/
2. Utwórz nowy projekt (lub użyj istniejącego)
3. Włącz **Google Drive API**:
   - APIs & Services → Enable APIs and Services
   - Szukaj "Google Drive API"
   - Kliknij "Enable"

4. Utwórz **Service Account**:
   - APIs & Services → Credentials
   - Create Credentials → Service Account
   - Nazwa: `railway-pdf-uploader`
   - Rola: Basic → Editor (lub bez roli)
   - Kliknij "Done"

5. Utwórz klucz JSON:
   - Kliknij na utworzone Service Account
   - Keys → Add Key → Create New Key
   - Typ: JSON
   - Pobierz plik (np. `service-account-key.json`)

### KROK 2: Dodaj credentiale do Railway

1. Otwórz pobrany plik JSON w edytorze tekstu
2. Skopiuj **całą zawartość** (pełny JSON)
3. W Railway:
   - Twój projekt → Variables
   - New Variable:
     - Name: `GOOGLE_DRIVE_CREDENTIALS_JSON`
     - Value: **[wklej skopiowany JSON]**

### KROK 3: Utwórz folder na Google Drive

1. Uruchom lokalnie (lub przez Railway CLI):
```bash
python google_drive_manager_railway.py
```

2. Jeśli folder nie istnieje, zostanie utworzony
3. Skopiuj **Folder ID** z wyniku (np. `1a2b3c4d5e6f7g8h9i0j`)

4. W Railway dodaj zmienną:
   - Name: `GOOGLE_DRIVE_FOLDER_ID`
   - Value: `[skopiowane Folder ID]`

### KROK 4: Sprawdź zmienne środowiskowe Railway

Upewnij się, że masz wszystkie:

```
DATABASE_URL=postgresql://...
BREVO_API_KEY=xkeysib-...
GOOGLE_DRIVE_CREDENTIALS_JSON={"type":"service_account",...}
GOOGLE_DRIVE_FOLDER_ID=1a2b3c4d5e6f7g8h9i0j
```

## 🔄 Używanie systemu PDF

### Metoda 1: Przez API (Recommended)

**Przetwórz wszystkie produkty bez Google Drive linków:**
```bash
curl -X POST "https://twoja-domena.railway.app/api/admin/process-pdfs" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Przetwórz konkretny produkt:**
```bash
curl -X POST "https://twoja-domena.railway.app/api/admin/process-pdfs?product_id=185871" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Przetwórz max 10 produktów (test):**
```bash
curl -X POST "https://twoja-domena.railway.app/api/admin/process-pdfs?limit=10" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Metoda 2: Przez Railway CLI

1. Zainstaluj Railway CLI:
```bash
npm i -g @railway/cli
```

2. Zaloguj się:
```bash
railway login
```

3. Połącz z projektem:
```bash
railway link
```

4. Uruchom skrypt:
```bash
# Test z pierwszym produktem
railway run python railway_pdf_processor.py test

# Wszystkie produkty
railway run python railway_pdf_processor.py all

# Konkretny produkt
railway run python railway_pdf_processor.py 185871
```

## 📊 Monitorowanie

### Sprawdź logi Railway:

1. W Railway Dashboard → Deployments → View Logs
2. Szukaj:
   - `✅ Uploaded to Google Drive` - sukces
   - `❌ Error` - błędy
   - `📥 Downloading PDF` - postęp

### Sprawdź bazę danych:

```sql
-- Produkty bez Google Drive linków
SELECT id, title, pdf_url 
FROM products 
WHERE pdf_url IS NOT NULL 
  AND google_drive_link IS NULL;

-- Produkty z Google Drive linkami
SELECT id, title, google_drive_link 
FROM products 
WHERE google_drive_link IS NOT NULL;
```

## 🎯 Przepływ po zakupie

1. **Klient kupuje produkt** → Stripe przetwarza płatność
2. **Zamówienie zapisane** → Order z product_id w bazie
3. **Email wysłany** → `send_order_confirmation_email()` w `email_utils.py`
4. **Link w emailu** → pobiera `google_drive_link` z Product
5. **Klient pobiera PDF** → bezpośrednio z Google Drive

## 🔧 Rozwiązywanie problemów

### "Google Drive not authenticated"
➡️ Sprawdź `GOOGLE_DRIVE_CREDENTIALS_JSON` w Railway Variables

### "No folder ID configured"
➡️ Dodaj `GOOGLE_DRIVE_FOLDER_ID` do Railway Variables

### "Error downloading PDF"
➡️ Sprawdź czy link w `pdf_url` działa (otwórz w przeglądarce)

### "Permission denied" w Google Drive
➡️ Upewnij się że Service Account ma dostęp do folderu

## 📝 Checklist wdrożenia

- [ ] Google Drive API włączone
- [ ] Service Account utworzone i klucz JSON pobrany
- [ ] `GOOGLE_DRIVE_CREDENTIALS_JSON` dodane do Railway
- [ ] Folder utworzony i `GOOGLE_DRIVE_FOLDER_ID` ustawione
- [ ] Test z jednym produktem przeszedł
- [ ] Email po zakupie zawiera Google Drive link
- [ ] System gotowy do produkcji! 🎉

## 💡 Wskazówki

### Automatyzacja
Możesz dodać do `main.py` automatyczne przetwarzanie po imporcie:
```python
# Po imporcie produktów
from railway_pdf_processor import RailwayPDFProcessor
processor = RailwayPDFProcessor()
processor.process_all_pending(limit=50)  # Przetwórz max 50
processor.close()
```

### Cron Job (Railway)
Ustaw cron job do regularnego przetwarzania:
```bash
# Co godzinę sprawdź nowe produkty
0 * * * * curl -X POST https://twoja-domena/api/admin/process-pdfs?limit=100
```

### Ograniczenia Google Drive
- **Free tier**: 15 GB storage
- **API limits**: 1000 requests/100s/user
- Wystarczy dla większości zastosowań
