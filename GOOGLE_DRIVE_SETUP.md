# Google Drive API Setup Guide

## Krok 1: Utwórz projekt w Google Cloud Console

1. Wejdź na: https://console.cloud.google.com/
2. Kliknij **"Create Project"** lub wybierz istniejący
3. Nazwij projekt np. "Manuals Store"
4. Kliknij **"Create"**

## Krok 2: Włącz Google Drive API

1. W menu bocznym wybierz: **APIs & Services** > **Library**
2. Wyszukaj: **"Google Drive API"**
3. Kliknij na nią i wybierz **"Enable"**

## Krok 3: Utwórz Service Account

1. Przejdź do: **APIs & Services** > **Credentials**
2. Kliknij **"Create Credentials"** > **"Service Account"**
3. Wypełnij dane:
   - **Service account name**: `manuals-store-uploader`
   - **Service account ID**: zostaw automatyczny
4. Kliknij **"Create and Continue"**
5. Role: wybierz **"Editor"** (lub można pominąć)
6. Kliknij **"Done"**

## Krok 4: Pobierz klucz JSON

1. W liście Service Accounts znajdź właśnie utworzone konto
2. Kliknij na email Service Account
3. Przejdź do zakładki **"Keys"**
4. Kliknij **"Add Key"** > **"Create new key"**
5. Wybierz format **JSON**
6. Kliknij **"Create"**
7. Plik JSON zostanie pobrany automatycznie

## Krok 5: Zainstaluj plik credentials

1. Zmień nazwę pobranego pliku na: `google_drive_credentials.json`
2. Skopiuj plik do folderu projektu:
   ```
   C:\Users\Sebek\Desktop\Strona Manuals\google_drive_credentials.json
   ```

## Krok 6: Zainstaluj wymagane biblioteki

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Krok 7: Test połączenia

Uruchom:
```bash
python google_drive_manager.py
```

Powinieneś zobaczyć: ✅ Google Drive authenticated successfully

## Struktura pliku credentials.json

Plik powinien zawierać:
```json
{
  "type": "service_account",
  "project_id": "manuals-store-xxxxx",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "manuals-store-uploader@...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

## Uwaga o limitach

- **Quota**: 1TB miejsca na darmowym koncie Google Drive
- **Prędkość**: ~100 plików/minutę
- **Wielkość pliku**: Max 5TB na plik

## Bezpieczeństwo

⚠️ **WAŻNE**: 
- Dodaj `google_drive_credentials.json` do `.gitignore`
- NIE udostępniaj tego pliku publicznie
- Trzymaj w bezpiecznym miejscu

## Dodatkowe opcje

### Współdzielenie folderu z innym kontem Google

Jeśli chcesz zarządzać plikami z normalnego konta Google:

1. Uruchom skrypt aby utworzyć folder
2. Skopiuj **Folder ID** z pliku `google_drive_config.json`
3. Wejdź na: https://drive.google.com/drive/folders/{FOLDER_ID}
4. Kliknij prawym przyciskiem > **Share**
5. Dodaj swój email Google i nadaj uprawnienia

## Troubleshooting

### Error: "The caller does not have permission"
- Upewnij się że Google Drive API jest włączone
- Sprawdź czy Service Account ma odpowiednie role

### Error: "Quota exceeded"
- Poczekaj kilka minut
- Sprawdź limity w Console: https://console.cloud.google.com/iam-admin/quotas

### Files not visible in my Drive
- To normalne! Service Account ma własne "Drive"
- Użyj opcji współdzielenia folderu (zobacz wyżej)
- Lub dostęp przez link który generuje skrypt
