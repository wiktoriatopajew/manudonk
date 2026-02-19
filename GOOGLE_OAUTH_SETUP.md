# 🔐 Google Drive OAuth 2.0 Setup Guide

## Dlaczego OAuth 2.0 zamiast Service Account?

Service Account nie ma własnej przestrzeni dyskowej na Google Drive. Musisz użyć swojego osobistego konta Google (OAuth 2.0) lub Google Workspace Shared Drive (płatne).

## Krok po kroku - utworzenie OAuth 2.0 credentials

### 1. Przejdź do Google Cloud Console
https://console.cloud.google.com/

### 2. Wybierz projekt
- Użyj istniejącego projektu (ten sam co Service Account)
- Lub utwórz nowy projekt

### 3. Włącz Google Drive API
- W menu wybierz: **APIs & Services** → **Library**
- Wyszukaj: **Google Drive API**
- Kliknij **Enable** (jeśli nie jest już włączone)

### 4. Utwórz OAuth 2.0 Client ID
- W menu wybierz: **APIs & Services** → **Credentials**
- Kliknij **+ CREATE CREDENTIALS**
- Wybierz: **OAuth client ID**

### 5. Skonfiguruj OAuth consent screen (jeśli pierwszy raz)
- User Type: **External** (dla osobistego konta)
- App name: `Manuals Store`
- User support email: Twój email
- Developer contact: Twój email
- Kliknij **Save and Continue**
- Scopes: pomiń (kliknij **Save and Continue**)
- Test users: dodaj swój email
- Kliknij **Save and Continue**

### 6. Utwórz Desktop App credentials
- Application type: **Desktop app**
- Name: `Manuals Store Desktop`
- Kliknij **Create**

### 7. Pobierz plik JSON
- Po utworzeniu zobaczysz dialog z Client ID i Client Secret
- Kliknij **DOWNLOAD JSON**
- Plik nazywa się coś jak: `client_secret_xxxxx.json`

### 8. Zmień nazwę i umieść w projekcie
```powershell
# Zmień nazwę na:
google_oauth_credentials.json

# Umieść w folderze:
C:\Users\Sebek\Desktop\Strona Manuals\
```

### 9. Uruchom setup OAuth
```powershell
python setup_google_oauth.py
```

To otworzy przeglądarkę gdzie:
1. Zalogujesz się swoim kontem Google
2. Zobaczysz warning "Google hasn't verified this app"
3. Kliknij **Advanced** → **Go to Manuals Store (unsafe)**
4. Kliknij **Continue**
5. Wybierz: Allow access to Google Drive

### 10. Gotowe!
Po autoryzacji plik `token.pickle` zostanie utworzony i będzie używany do wszystkich przyszłych uploadów.

---

## ⚠️ Ważne

- **OAuth 2.0** używa **Twojej** przestrzeni dyskowej na Google Drive
- Masz **15 GB** za darmo (Google One można rozszerzyć)
- Token jest ważny długo (refresh token odnawia się automatycznie)
- Jedna autoryzacja wystarczy na zawsze

---

## 🔄 Troubleshooting

### "App isn't verified"
To normalne dla apps w trybie testowym. Kliknij Advanced → Continue.

### "This app is blocked"
Idź do: https://myaccount.google.com/permissions
Usuń aplikację i spróbuj ponownie.

### Token wygasł
Usuń `token.pickle` i uruchom `python setup_google_oauth.py` ponownie.

---

## 🚀 Po setupie

```powershell
# Przetestuj upload
python test_upload.py

# Przetwórz wszystkie PDFy
python process_pdfs.py full

# Zaktualizuj bazę danych
python update_database.py
```
