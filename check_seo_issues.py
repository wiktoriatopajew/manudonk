"""
Diagnoza problemów SEO na manualbear.com
"""
import requests
from bs4 import BeautifulSoup

print("=" * 80)
print("DIAGNOZA SEO - manualbear.com")
print("=" * 80)
print()

issues = []
successes = []

# 1. Sprawdź robots.txt
print("1. Sprawdzam robots.txt...")
try:
    r = requests.get("https://manualbear.com/robots.txt")
    if r.status_code == 200:
        if "Sitemap:" in r.text:
            successes.append("✅ robots.txt istnieje i zawiera sitemap")
        else:
            issues.append("❌ robots.txt nie zawiera linku do sitemap")
        
        if "Disallow: /manuals/" in r.text:
            issues.append("❌ KRYTYCZNE: robots.txt blokuje /manuals/ - produkty nie są indeksowane!")
    else:
        issues.append(f"❌ robots.txt zwraca błąd {r.status_code}")
except Exception as e:
    issues.append(f"❌ Błąd: {e}")

# 2. Sprawdź sitemap.xml
print("2. Sprawdzam sitemap.xml...")
try:
    r = requests.get("https://manualbear.com/sitemap.xml")
    if r.status_code == 200:
        count = r.text.count("<loc>")
        successes.append(f"✅ sitemap.xml działa ({count} URLi)")
        
        if count < 10:
            issues.append(f"⚠️  Tylko {count} URLi w sitemap - za mało!")
    else:
        issues.append(f"❌ sitemap.xml zwraca błąd {r.status_code}")
except Exception as e:
    issues.append(f"❌ Błąd: {e}")

# 3. Sprawdź stronę główną
print("3. Sprawdzam stronę główną...")
try:
    r = requests.get("https://manualbear.com")
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Title
    title = soup.find('title')
    if title and len(title.text) > 10:
        successes.append(f"✅ Title: {title.text[:60]}...")
    else:
        issues.append("❌ Brak odpowiedniego title")
    
    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc = meta_desc['content']
        successes.append(f"✅ Meta description: {desc[:60]}...")
        
        # Check if Polish
        if 'Find' in desc or 'Over' in desc:
            issues.append("⚠️  Meta description po angielsku - powinno być po polsku!")
    else:
        issues.append("❌ Brak meta description")
    
    # H1
    h1 = soup.find('h1')
    if h1:
        successes.append(f"✅ H1: {h1.text[:60]}...")
    else:
        issues.append("❌ Brak H1 na stronie głównej")
    
    # Schema.org
    if 'schema.org' in r.text:
        successes.append("✅ Structured data (schema.org) obecne")
    else:
        issues.append("❌ Brak structured data")
        
except Exception as e:
    issues.append(f"❌ Błąd: {e}")

# 4. Sprawdź przykładowy produkt
print("4. Sprawdzam przykładowy produkt...")
try:
    # Get first product from sitemap
    r = requests.get("https://manualbear.com/sitemap.xml")
    soup = BeautifulSoup(r.text, 'xml')
    locs = soup.find_all('loc')
    product_urls = [loc.text for loc in locs if '/manuals/' in loc.text]
    
    if product_urls:
        product_url = product_urls[0]
        print(f"   Sprawdzam: {product_url}")
        
        r = requests.get(product_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Title
        title = soup.find('title')
        if title and len(title.text) > 20:
            successes.append(f"✅ Produkt ma title: {title.text[:60]}...")
        else:
            issues.append("❌ Produkty nie mają odpowiednich title")
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            successes.append(f"✅ Produkt ma meta description")
        else:
            issues.append("❌ Produkty nie mają meta description")
        
        # Schema.org Product
        if 'schema.org/Product' in r.text:
            successes.append("✅ Produkty mają structured data (Product)")
        else:
            issues.append("❌ Produkty nie mają Product structured data")
    else:
        issues.append("❌ Brak produktów w sitemap!")
        
except Exception as e:
    issues.append(f"❌ Błąd: {e}")

# Podsumowanie
print()
print("=" * 80)
print("SUKCESY:")
print("=" * 80)
for s in successes:
    print(s)

print()
print("=" * 80)
print("PROBLEMY DO NAPRAWY:")
print("=" * 80)
for i in issues:
    print(i)

print()
print("=" * 80)
print("GŁÓWNE PRZYCZYNY BRAKU WIDOCZNOŚCI W GOOGLE:")
print("=" * 80)

if any("po angielsku" in i for i in issues):
    print("1. ❌ Treści po angielsku zamiast po polsku")
    print("   → Google.pl preferuje polskie treści")

if any("blokuje /manuals/" in i for i in issues):
    print("2. ❌ robots.txt blokuje indeksowanie produktów")
    print("   → KRYTYCZNE - Google nie może indeksować produktów!")

print("3. ⚠️  Prawdopodobnie brak zgłoszenia do Google Search Console")
print("   → Musisz dodać stronę i sitemap w GSC")

print("4. ⚠️  Może brakować linków zewnętrznych (backlinks)")
print("   → Google potrzebuje sygnałów że strona jest wartościowa")

print()
print("=" * 80)
print("CO ZROBIĆ:")
print("=" * 80)
print("1. Zmień meta descriptions na polski")
print("2. Dodaj stronę do Google Search Console")
print("3. Zgłoś sitemap w GSC")
print("4. Zbuduj kilka linków zewnętrznych")
print("5. Sprawdź czy domena jest zindeksowana: site:manualbear.com w Google")
