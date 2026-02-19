# 🎨 Stripe Checkout - Przewodnik Brandingu

## ✅ Co zostało zaimplementowane w kodzie

### 1. **Obrazy produktów w Checkout**
- ✅ Każdy produkt w koszyku teraz wyświetla swoje zdjęcie
- ✅ Automatycznie pobiera pierwszy obraz z `image_url`
- ✅ Konwertuje relatywne ścieżki na pełne URL
- ✅ Działa zarówno dla pojedynczych jak i wielu produktów

### 2. **Ulepszone opisy**
- ✅ Wyświetla markę i model produktu
- ✅ Pokazuje kwotę rabatu jeśli zastosowano kod
- ✅ Zgodne z limitami Stripe (250 znaków nazwa, 350 opis)

---

## 🎨 Konfiguracja Brandingu w Stripe Dashboard

### Krok 1: Zaloguj się do Stripe Dashboard
1. Przejdź do: https://dashboard.stripe.com/
2. Zaloguj się do swojego konta

### Krok 2: Otwórz ustawienia brandingu
1. W lewym menu kliknij **Settings** (⚙️)
2. Wybierz **Branding**
3. Lub bezpośrednio: https://dashboard.stripe.com/settings/branding

### Krok 3: Skonfiguruj swój branding

#### **Logo i Ikona**
```
┌─────────────────────────────────────┐
│ Brand icon (favicon)                │
│ • Format: PNG, JPG, SVG             │
│ • Rozmiar: min 128x128 px           │
│ • Zalecane: 512x512 px kwadrat      │
│ • Wyświetla się w karcie przegląd.  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Brand logo                          │
│ • Format: PNG, JPG, SVG             │
│ • Rozmiar: max 400 KB               │
│ • Zalecane: przezroczyste tło       │
│ • Wyświetla się na górze checkout   │
└─────────────────────────────────────┘
```

#### **Kolory**
```
┌─────────────────────────────────────┐
│ Brand color (główny kolor)          │
│ • Używany dla przycisków            │
│ • Linki i elementy interaktywne     │
│ • Zalecane: kolor z Twojej strony   │
│   Przykład: #2563eb (niebieski)     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Accent color (kolor akcentowy)      │
│ • Używany dla stanów hover          │
│ • Fokus na polach                   │
│ • Zalecane: ciemniejszy odcień      │
│   Przykład: #1e40af                 │
└─────────────────────────────────────┘
```

#### **Czcionka**
```
┌─────────────────────────────────────┐
│ Custom font (opcjonalne)            │
│ • Możesz wybrać z listy Stripe:     │
│   - Inter (nowoczesna, czytelna)    │
│   - Source Code Pro                 │
│   - Work Sans                       │
│ • LUB użyć domyślnej Stripe         │
└─────────────────────────────────────┘
```

#### **Motyw**
```
┌─────────────────────────────────────┐
│ Theme (jasny/ciemny)                │
│ • Light - jasne tło (zalecane)      │
│ • Dark - ciemne tło                 │
│ • Auto - dopasowanie do systemu     │
└─────────────────────────────────────┘
```

---

## 🖼️ Jak przygotować grafikę

### Logo (zalecane wymiary):
```
┌────────────────────────┐
│                        │
│    [TWOJE LOGO]        │  ← 400-600 px szerokość
│                        │
└────────────────────────┘
     ↑ 100-150 px
```
- **Format**: PNG z przezroczystym tłem
- **Szerokość**: 400-600 px
- **Wysokość**: 100-150 px (nie za wysokie!)
- **Rozmiar**: max 400 KB

### Favicon:
```
┌─────┐
│ [M] │  ← 512x512 px kwadrat
└─────┘
```
- **Format**: PNG lub SVG
- **Rozmiar**: 512x512 px (kwadrat)
- **Ikona**: Prosta, rozpoznawalna przy małym rozmiarze

---

## 🎨 Przykładowa konfiguracja dla ManualBear

### Sugerowane kolory:
```css
Brand color:  #2563eb   /* Profesjonalny niebieski */
Accent color: #1e40af   /* Ciemniejszy niebieski */
Background:   #ffffff   /* Białe tło (light theme) */
```

### Sugerowany tekst:
```
Company name: ManualBear
Tagline: Professional Service Manuals & Repair Guides
```

---

## 📱 Jak wygląda Checkout po konfiguracji

```
┌────────────────────────────────────────────┐
│  [LOGO MANUALBEAR]                    [X]  │
│                                            │
│  Pay ManualBear                            │
│  ┌──────────────────────────────────────┐ │
│  │ 📧 Email                             │ │
│  │ customer@example.com                 │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ 💳 Card information                  │ │
│  │ 1234 5678 9012 3456                  │ │
│  │ MM/YY  CVC                           │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ 🛒 Order summary                     │ │
│  │                                      │ │
│  │ [IMG] Ford F-150 Manual     $12.99  │ │ ← ZDJĘCIE PRODUKTU
│  │ [IMG] BMW E46 Manual        $14.99  │ │
│  │                                      │ │
│  │ Subtotal                    $27.98  │ │
│  │ Discount (WELCOME10)        -$2.80  │ │
│  │ ────────────────────────────────────│ │
│  │ Total                       $25.18  │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  [ Pay $25.18 ]  ← Button w Twoim kolorze │
│                                            │
│  🔒 Powered by Stripe                     │
└────────────────────────────────────────────┘
```

---

## 🚀 Testowanie

### 1. **Test w trybie testowym**
```bash
# W Stripe Dashboard przełącz na "Test mode"
# Użyj testowej karty:
Numer:  4242 4242 4242 4242
Ważność: 12/34
CVC:    123
ZIP:    12345
```

### 2. **Podgląd na żywo**
- Stwórz testowy checkout z Twojej strony
- Sprawdź jak wyglądają obrazy i kolory
- Przetestuj na telefonie i desktopie

---

## 💡 Dodatkowe wskazówki

### ✅ Co działa dobrze:
- Proste, czytelne logo bez zbyt wielu detali
- Kontrast między kolorem przycisku a tłem
- Zdjęcia produktów w wysokiej jakości (min 800x800 px)
- Jasny motyw dla lepszej czytelności

### ❌ Czego unikać:
- Za wysokiego logo (zasłania formularz)
- Zbyt jasnych kolorów (słaba widoczność)
- Zbyt dużych plików (spowalniają ładowanie)
- Niskiej jakości zdjęć produktów

---

## 📊 Zaawansowane opcje (opcjonalne)

### Custom Success/Cancel Pages
Już masz skonfigurowane w kodzie:
```python
success_url=DOMAIN + '/success?session_id={CHECKOUT_SESSION_ID}'
cancel_url=DOMAIN + '/cart'
```

### Email Notifications
Stripe automatycznie wysyła:
- Potwierdzenie płatności do klienta
- Paragon (receipt)
- Możesz je dostosować w: **Settings → Emails**

---

## 🎯 Wynik

Po skonfigurowaniu:
1. ✅ Użytkownicy widzą Twoje logo i kolory
2. ✅ Każdy produkt ma swoje zdjęcie
3. ✅ Profesjonalny, spójny wygląd z Twoją stroną
4. ✅ Zwiększone zaufanie i wyższe konwersje

---

**Pytania?** Daj znać jeśli potrzebujesz pomocy z grafiką lub konfiguracją! 🚀
