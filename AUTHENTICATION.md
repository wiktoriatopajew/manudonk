# Manuals Store - Complete E-commerce Platform

## ✨ Nowe Funkcje (v2.0.0)

### 🔐 System Autentykacji
- **Rejestracja użytkowników** z emailem i hasłem
- **Weryfikacja email** przez kod 6-cyfrowy
- **Logowanie** z tokenami JWT
- **Panel administratora** do zarządzania

### 📋 Dostępne Strony

#### Użytkownik:
- `/register` - Rejestracja
- `/login` - Logowanie
- `/verify-email` - Weryfikacja emaila

#### Polityki:
- `/privacy-policy` - Polityka prywatności
- `/terms-of-service` - Regulamin
- `/refund-policy` - Polityka zwrotów

#### Admin:
- `/admin` - Panel administratora (wymaga uprawnień admin)

### 🔧 Konfiguracja Email

W trybie deweloperskim kody weryfikacyjne są wyświetlane w konsoli.

Aby skonfigurować prawdziwe wysyłanie emaili, ustaw zmienne środowiskowe:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=twoj-email@gmail.com
SMTP_PASSWORD=twoje-haslo-aplikacji
FROM_EMAIL=noreply@twoj-sklep.com
```

### 👤 Tworzenie Admina

Aby utworzyć pierwszego użytkownika z uprawnieniami administratora, uruchom:

```python
from database.models import User, get_session

session = get_session()
try:
    # Znajdź użytkownika po emailu
    user = session.query(User).filter(User.email == "admin@example.com").first()
    if user:
        user.is_admin = True
        user.is_verified = True  # Opcjonalnie
        session.commit()
        print("Admin created!")
finally:
    session.close()
```

### 🔄 Aktualizacja Bazy Danych

Jeśli masz już istniejącą bazę danych, uruchom:

```bash
python init_db.py
```

To utworzy nowe tabele (users, verification_codes, orders) bez usuwania produktów.

### 🛒 Proces Zamawiania

1. Użytkownik przegląda produkty
2. Klika "Kup" na stronie produktu
3. Wpisuje email
4. Płaci przez PayPal
5. Zamówienie zostaje zapisane w bazie
6. Email z potwierdzeniem jest wysyłany

### 🎨 Nowy Design

- Gradientowe tło na stronie głównej
- Animowane elementy
- Glassmorphism na formularzach
- Responsive design

### 📊 API Endpoints

#### Publiczne:
- `POST /api/auth/register` - Rejestracja
- `POST /api/auth/login` - Logowanie
- `POST /api/auth/verify-email` - Weryfikacja
- `POST /api/auth/resend-code` - Ponowne wysłanie kodu

#### Wymaga autentykacji:
- `GET /api/auth/me` - Informacje o użytkowniku

#### Tylko admin:
- `GET /api/auth/admin/users` - Lista użytkowników
- `GET /api/auth/admin/orders` - Lista zamówień

### 🔒 Bezpieczeństwo

- Hasła zahashowane bcrypt
- Tokeny JWT z wygaśnięciem
- Kody weryfikacyjne z limitem czasowym (15 min)
- HTTPS recommended dla produkcji

---

**Dokumentacja techniczna znajduje się w plikach:**
- `README.md` - Główny opis (po polsku)
- `SEO_GUIDE.md` - Przewodnik SEO
- `QUICKSTART.md` - Szybki start
