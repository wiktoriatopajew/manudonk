# Shoparize — Shopify Integration
# Zamień 4245 na swój numer z panelu Shoparize

---

## BLOK 1 — Strona potwierdzenia zamówienia (Thank You page)
### Gdzie wkleić:
Shopify Admin → Settings → Checkout → przewiń na dół → "Order status page" → pole "Additional scripts"

```html
<script src="https://partner-cdn.shoparize.com/js/shoparize.js" defer="defer"></script>
<script>
window.dataLayerShoparize = window.dataLayerShoparize || [];
dataLayerShoparize.push({
    event: "purchase",
    ecommerce: {
        transaction_id: "{{ checkout.order_number }}",
        value: {{ checkout.total_price | divided_by: 100.0 }},
        tax: {{ checkout.tax_price | divided_by: 100.0 }},
        shipping: {{ checkout.shipping_price | divided_by: 100.0 }},
        currency: "{{ checkout.currency }}",
        items: [
            {% for line_item in checkout.line_items %}
            {
                item_id: "{{ line_item.product_id }}",
                item_name: "{{ line_item.title | remove: "'" | remove: '"' }}",
                currency: "{{ checkout.currency }}",
                price: {{ line_item.final_price | divided_by: 100.0 }},
                quantity: {{ line_item.quantity }}
            }{% unless forloop.last %},{% endunless %}
            {% endfor %}
        ]
    }
});
</script>
<script>
    window.addEventListener('load', function () {
        SHOPARIZE_API().conv(4245);
    });
</script>
```

---

## BLOK 2 — Wszystkie inne strony (home, kategorie, produkty)
### Gdzie wkleić:
Shopify Admin → Online Store → Themes → Actions → Edit code → Layout → **theme.liquid**
Wklej tuż przed zamykającym tagiem `</body>`

```html
{% unless request.page_type == 'thankyou' %}
<script src="https://partner-cdn.shoparize.com/js/shoparize.js" defer="defer"></script>
<script>
    window.addEventListener('load', function () {
        SHOPARIZE_API().init(4245);
    });
</script>
{% endunless %}
```

---

## Co zmienić:
- `4245` → wstaw swój numer z panelu Shoparize (np. `1234`)
- Oba bloki mają TEN SAM Shop ID

## Uwagi:
- Blok 1: używa `checkout.*` (nie `order.*`) — to poprawna składnia dla Shopify Additional Scripts
- Blok 1: `divided_by: 100.0` zamiast `times: 0.01` — dokładniejsze dla cen w centach
- Blok 1: pętla `{% for line_item in checkout.line_items %}` — oryginalny kod Shoparize tego nie miał!
- Blok 2: `{% unless request.page_type == 'thankyou' %}` — zabezpieczenie żeby init nie odpał na thank you page
