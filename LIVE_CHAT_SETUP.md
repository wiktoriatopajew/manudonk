# Live Chat Setup Guide (Tawk.to)

## What is Tawk.to?
Darmowy widget live chat dla strony - pozwala rozmawiać z klientami w czasie rzeczywistym.

## Setup Instructions

### 1. Utwórz konto Tawk.to
1. Wejdź na https://www.tawk.to
2. Kliknij "Sign Up Free"
3. Zarejestruj się (email + hasło)

### 2. Dodaj swoją stronę
1. Po zalogowaniu kliknij "Add Property"
2. Wpisz nazwę: "Manuals Store"
3. URL: `localhost:8000` (na razie) lub `yourdomain.com` (produkcja)
4. Wybierz kategorie: "E-commerce"

### 3. Pobierz kod widgetu
1. Przejdź do Dashboard → Administration
2. Kliknij "Channels" → "Chat Widget"
3. Skopiuj kod JavaScript (wygląda tak):
```javascript
var Tawk_API=Tawk_API||{}, Tawk_LoadStart=new Date();
(function(){
var s1=document.createElement("script"),s0=document.getElementsByTagName("script")[0];
s1.async=true;
s1.src='https://embed.tawk.to/TWÓJ_ID/TWÓJ_WIDGET_ID';
s1.charset='UTF-8';
s1.setAttribute('crossorigin','*');
s0.parentNode.insertBefore(s1,s0);
})();
```

### 4. Dodaj kod do strony
Otwórz plik `templates/base.html` i znajdź sekcję z kodem Tawk.to (przed `</body>`).
Zamień `YOUR_PROPERTY_ID` i `YOUR_WIDGET_ID` na prawdziwe wartości z Tawk.to.

### 5. Personalizacja widgetu
W panelu Tawk.to możesz:
- Zmienić kolory (purple/blue żeby pasowały do strony)
- Dodać logo
- Ustawić przywitanie: "Hi! Need help finding a manual?"
- Dodać szybkie odpowiedzi (Quick Replies):
  - "How long is delivery?" → "1-5 minutes"
  - "What payment methods?" → "Credit card via Stripe"
  - "How to download?" → "Check your email after purchase"

### 6. Aplikacja mobilna
Pobierz aplikację Tawk.to (iOS/Android) żeby odpowiadać klientom z telefonu!

## Features (Wszystko za darmo!)
✅ Unlimited chats
✅ Unlimited agents
✅ Mobile apps
✅ Visitor monitoring (widzisz kto jest na stronie)
✅ File sharing
✅ Pre-chat forms
✅ Canned responses (szablony odpowiedzi)
✅ Chat history
✅ Knowledge base (opcjonalne FAQ)

## Pro Tips
1. **Auto-greeting**: Ustaw automatyczne przywitanie po 10 sekundach
2. **Away message**: "We're offline now. Leave a message and we'll respond within 24h"
3. **Trigger messages**: Pokaż message jeśli użytkownik spędził >30s na stronie produktu
4. **Monitor keywords**: Alert gdy ktoś pisze "price", "discount", "refund"

## Wyłączenie (jeśli nie chcesz)
Skomentuj kod w `base.html`:
```html
<!-- Tawk.to temporarily disabled
<script type="text/javascript">
...
</script>
-->
```

## Produkcja
Pamiętaj zaktualizować Property URL w Tawk.to na prawdziwą domenę!
