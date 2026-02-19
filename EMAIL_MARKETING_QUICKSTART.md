# 🚀 Email Marketing - Quick Start

## Setup (10 minut)

### 1. Migracja Bazy Danych
```powershell
cd "C:\Users\Sebek\Desktop\Strona Manuals"
.venv\Scripts\python.exe migrate_email_marketing.py
```

### 2. Restart Serwera
Serwer powinien automatycznie się zrestartować. Jeśli nie:
```powershell
# Zatrzymaj obecny serwer (Ctrl+C)
# Uruchom ponownie:
& "C:/Users/Sebek/Desktop/Strona Manuals/.venv/Scripts/python.exe" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Sprawdź czy działa
1. Odwiedź stronę główną: http://localhost:8000
2. Popup pojawi się po 5 sekundach
3. Zapisz się z testowym emailem
4. Sprawdź terminal - powinien być log z wysłaniem emaila
5. Sprawdź czy kod działa w koszyku

## Admin Panel (5 minut)

### 1. Zaloguj się jako Admin
http://localhost:8000/login

### 2. Przejdź do Newsletter Panel
http://localhost:8000/admin/newsletter

### 3. Zobacz Subskrybentów
- Zakładka "Subscribers"
- Filtruj: All / Active / Purchased / Not Purchased

## Pierwsza Kampania (10 minut)

### 1. Utwórz Kampanię
1. Zakładka "Create Campaign"
2. Wypełnij:
   - Name: "Test Campaign"
   - Subject: "Hello from Manuals Store!"
   - Segment: "All Subscribers"
   - Content: (użyj przykładu poniżej)

### 2. Przykładowy Prosty Email
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial; background: #1f2937; padding: 20px; margin: 0;">
    <div style="max-width: 600px; margin: 0 auto; background: #111827; border-radius: 12px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #3b82f6, #06b6d4); padding: 40px; text-align: center;">
            <h1 style="color: white; margin: 0;">Witaj w Manuals Store! 👋</h1>
        </div>
        <div style="padding: 30px; color: #e5e7eb;">
            <p>Dziękujemy za zapis do naszego newslettera!</p>
            <p><strong>Masz już swój kod rabatowy 10%</strong> - możesz go użyć w każdej chwili.</p>
            <p>Przeglądaj nasze manuały:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:8000" style="display: inline-block; background: linear-gradient(135deg, #3b82f6, #06b6d4); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    Zobacz Produkty →
                </a>
            </div>
            <p style="color: #9ca3af; font-size: 14px;">Pozdrawiamy,<br>Zespół Manuals Store</p>
        </div>
    </div>
</body>
</html>
```

### 3. Wyślij Kampanię
1. Kliknij "Create Campaign"
2. Przejdź do zakładki "Campaigns"
3. Kliknij "Send Now" przy kampanii
4. Potwierdź wysyłkę
5. Zobacz wynik: "Campaign sent to X subscribers"

### 4. Zobacz Statystyki
1. Kliknij "View Stats" przy wysłanej kampanii
2. Zobacz:
   - Total Sent
   - Opened
   - Clicked
   - Open Rate %
   - Click Rate %

## Automatyzacja (5 minut)

### Test Ręczny
```powershell
.venv\Scripts\python.exe email_automation.py
```

Powinieneś zobaczyć:
```
🚀 Starting email automation tasks...
==================================================
🛒 Found 0 abandoned carts to process
✅ Abandoned cart reminders completed

📧 Found 0 subscribers to remind about discount code
✅ Discount reminders completed

==================================================
✅ Email automation completed!
```

### Harmonogram (Windows Task Scheduler)
Aby uruchamiać automatycznie codziennie o 10:00:

1. Wyszukaj "Task Scheduler" w Windows
2. Kliknij "Create Basic Task"
3. Nazwa: "Email Marketing Daily"
4. Trigger: Daily, co 1 dzień, 10:00 AM
5. Action: Start a program
   - Program/script: `C:\Users\Sebek\Desktop\Strona Manuals\.venv\Scripts\python.exe`
   - Add arguments: `email_automation.py`
   - Start in: `C:\Users\Sebek\Desktop\Strona Manuals`
6. Kliknij Finish

## Testowanie Porzuconych Koszyków

### 1. Utwórz Porzucony Koszyk
1. Odwiedź stronę główną
2. Dodaj produkty do koszyka
3. **NIE** dokończ zakupu - zamknij stronę
4. Poczekaj 24 godziny (lub zmień w kodzie dla testu)

### 2. Uruchom Automation
```powershell
.venv\Scripts\python.exe email_automation.py
```

### 3. Sprawdź Email
Powinieneś dostać email z:
- Listą produktów w koszyku
- Dodatkowym 5% rabatem
- Linkiem do dokończenia zakupu

## Testowanie Przypomnień o Kodzie

### 1. Zapisz się do Newslettera
Użyj nowego emaila.

### 2. Nie Kupuj Przez 7 Dni
Lub zmień w `email_automation.py`:
```python
cutoff_time = datetime.utcnow() - timedelta(days=7)
# Zmień na dla testu:
cutoff_time = datetime.utcnow() - timedelta(minutes=1)
```

### 3. Uruchom Automation
```powershell
.venv\Scripts\python.exe email_automation.py
```

### 4. Sprawdź Email
Powinieneś dostać przypomnienie o kodzie WELCOMEXXXXXX.

## Segmentacja w Praktyce

### Przykładowe Kampanie

**1. Dla Wszystkich (All)**
- Ogłoszenia nowych produktów
- Sezonowe promocje
- Nowości w sklepie

**2. Dla Kupujących (Purchased)**
- Cross-sell: "Kupiłeś manual do BMW? Zobacz też dla Audi"
- Upsell: "Upgrade do wersji Professional"
- Loyalty: "Dziękujemy za zakup! Oto 15% na następny"

**3. Dla Niekupujących (Not Purchased)**
- Dodatkowy rabat: "Użyj kod EXTRA15 z 10%"
- Przypomnienie: "Twój kod wciąż czeka!"
- Testimonials: "Zobacz co mówią inni klienci"

## Monitoring i Optymalizacja

### Sprawdzaj Regularnie
1. Open Rate - cel: >20%
2. Click Rate - cel: >3%
3. Conversion Rate - % zakupów

### Jeśli Open Rate niski:
- ✅ Lepszy temat emaila (krótki, konkretny, z emoji)
- ✅ Inny czas wysyłki
- ✅ Segment lepiej

### Jeśli Click Rate niski:
- ✅ Wyraźniejsze CTA buttony
- ✅ Lepszy content
- ✅ Silniejsza oferta

## Najczęstsze Pytania

### Q: Jak często wysyłać kampanie?
**A:** Raz w tygodniu normalnie, 2-3 razy w miesiącu dla promocji. Nie spamuj!

### Q: Czy mogę testować przed wysłaniem?
**A:** Tak! Użyj przycisku "Preview" lub wyślij do siebie jako test segment.

### Q: Co jeśli ktoś chce się wypisać?
**A:** Dodaj link w emailu:
```html
<a href="mailto:wiktoriatopajew@gmail.com?subject=Unsubscribe">Wypisz się</a>
```
Lub zaimplementuj endpoint /unsubscribe.

### Q: Jak dodać obrazki?
**A:** Hostuj na zewnętrznych serwerach (Imgur, Cloudinary) i użyj:
```html
<img src="https://i.imgur.com/image.jpg" style="max-width: 100%; height: auto;">
```

### Q: Tracking działa?
**A:** Sprawdź w Statistics kampanii. Pixel ładuje się gdy email otwarty.

## Next Steps

1. **Zaimplementuj unsubscribe** - link do wypisania
2. **A/B Testing** - testuj różne tematy
3. **Email Templates Library** - gotowe szablony
4. **Analytics Dashboard** - wykresy i statystyki
5. **GDPR Compliance** - eksport danych, privacy policy

## Support

Zobacz pełną dokumentację: [EMAIL_MARKETING_GUIDE.md](EMAIL_MARKETING_GUIDE.md)
