"""
Diagnoza SEO dla manualdonkey.com
"""
import requests
from bs4 import BeautifulSoup

DOMAIN = "https://manualdonkey.com"

print("=" * 80)
print(f"DIAGNOZA SEO - {DOMAIN}")
print("=" * 80)
print()

issues = []
successes = []
warnings = []

# 1. Sprawdź robots.txt
print("1️⃣  Sprawdzam robots.txt...")
try:
    r = requests.get(f"{DOMAIN}/robots.txt", timeout=10)
    if r.status_code == 200:
        content = r.text
        if "Sitemap:" in content:
            successes.append("✅ robots.txt istnieje i zawiera sitemap")
        else:
            issues.append("❌ robots.txt nie zawiera linku do sitemap")
        
        if "Disallow: /manuals/" in content or "Disallow: /manuals" in content:
            issues.append("❌ KRYTYCZNE: robots.txt blokuje /manuals/ - produkty nie będą indeksowane!")
        else:
            successes.append("✅ Produkty (/manuals/) są dostępne dla robotów")
            
        if "Allow: /manuals/" in content:
            successes.append("✅ Jawne Allow: /manuals/ w robots.txt")
    else:
        issues.append(f"❌ robots.txt zwraca błąd {r.status_code}")
except Exception as e:
    issues.append(f"❌ Błąd robots.txt: {e}")

# 2. Sprawdź sitemap.xml
print("2️⃣  Sprawdzam sitemap.xml...")
try:
    r = requests.get(f"{DOMAIN}/sitemap.xml", timeout=10)
    if r.status_code == 200:
        count = r.text.count("<loc>")
        successes.append(f"✅ sitemap.xml działa ({count} URLi)")
        
        if count < 10:
            warnings.append(f"⚠️  Tylko {count} URLi w sitemap - może być za mało")
        elif count > 1000:
            successes.append(f"✅ Duży sitemap ({count} produktów)")
            
        # Sprawdź czy są produkty
        if "/manuals/" in r.text:
            successes.append("✅ Sitemap zawiera linki do produktów (/manuals/)")
        else:
            issues.append("❌ Sitemap nie zawiera linków do produktów!")
    else:
        issues.append(f"❌ sitemap.xml zwraca błąd {r.status_code}")
except Exception as e:
    issues.append(f"❌ Błąd sitemap.xml: {e}")

# 3. Sprawdź stronę główną
print("3️⃣  Sprawdzam stronę główną...")
try:
    r = requests.get(DOMAIN, timeout=10)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Title
        title = soup.find('title')
        if title:
            title_text = title.text.strip()
            if len(title_text) > 0:
                successes.append(f"✅ Title: {title_text[:60]}...")
                if len(title_text) > 60:
                    warnings.append(f"⚠️  Title długość: {len(title_text)} znaków (optymalne: 50-60)")
            else:
                issues.append("❌ Pusty title")
        else:
            issues.append("❌ Brak tagu <title>")
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc = meta_desc.get('content').strip()
            if desc:
                successes.append(f"✅ Meta description: {desc[:60]}...")
                if len(desc) > 160:
                    warnings.append(f"⚠️  Description długość: {len(desc)} (optymalne: 150-160)")
            else:
                issues.append("❌ Pusta meta description")
        else:
            issues.append("❌ Brak meta description")
        
        # Open Graph
        og_title = soup.find('meta', property='og:title')
        if og_title:
            successes.append("✅ Open Graph title obecny")
        else:
            warnings.append("⚠️  Brak og:title (dla social media)")
            
        # H1
        h1 = soup.find('h1')
        if h1:
            successes.append(f"✅ H1: {h1.text.strip()[:50]}...")
        else:
            warnings.append("⚠️  Brak H1 na stronie głównej")
            
        # Canonical
        canonical = soup.find('link', rel='canonical')
        if canonical:
            successes.append(f"✅ Canonical URL: {canonical.get('href')}")
        else:
            warnings.append("⚠️  Brak canonical URL")
            
    else:
        issues.append(f"❌ Strona główna zwraca błąd {r.status_code}")
except Exception as e:
    issues.append(f"❌ Błąd strony głównej: {e}")

# 4. Sprawdź przykładową stronę produktu
print("4️⃣  Sprawdzam przykładową stronę produktu...")
try:
    # Najpierw pobierz sitemap aby znaleźć produkt
    r = requests.get(f"{DOMAIN}/sitemap.xml", timeout=10)
    if r.status_code == 200:
        # Znajdź pierwszy URL produktu
        soup_sitemap = BeautifulSoup(r.text, 'xml')
        product_urls = [loc.text for loc in soup_sitemap.find_all('loc') if '/manuals/' in loc.text]
        
        if product_urls:
            product_url = product_urls[0]
            print(f"   Testuję: {product_url}")
            
            r_prod = requests.get(product_url, timeout=10)
            if r_prod.status_code == 200:
                soup = BeautifulSoup(r_prod.text, 'html.parser')
                
                # Title
                title = soup.find('title')
                if title and title.text.strip():
                    successes.append(f"✅ Produkt ma title")
                else:
                    issues.append("❌ Produkty nie mają title")
                
                # Meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content', '').strip():
                    successes.append(f"✅ Produkt ma meta description")
                else:
                    issues.append("❌ Produkty nie mają meta description")
                    
                # Structured data (JSON-LD)
                json_ld = soup.find('script', type='application/ld+json')
                if json_ld:
                    successes.append("✅ Produkty mają structured data (Schema.org)")
                else:
                    warnings.append("⚠️  Brak structured data (Schema.org) - dodaj dla lepszych rich snippets")
                    
            else:
                warnings.append(f"⚠️  Strona produktu zwraca {r_prod.status_code}")
        else:
            warnings.append("⚠️  Nie znaleziono produktów w sitemap")
except Exception as e:
    warnings.append(f"⚠️  Błąd sprawdzania produktu: {e}")

# 5. Sprawdź HTTPS
print("5️⃣  Sprawdzam HTTPS...")
if DOMAIN.startswith("https://"):
    successes.append("✅ Strona używa HTTPS")
else:
    issues.append("❌ Strona nie używa HTTPS!")

# 6. Sprawdź mobile-friendly
print("6️⃣  Sprawdzam mobile viewport...")
try:
    r = requests.get(DOMAIN, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if viewport:
        successes.append("✅ Meta viewport skonfigurowany (mobile-friendly)")
    else:
        warnings.append("⚠️  Brak meta viewport - może źle wyglądać na mobile")
except:
    pass

# PODSUMOWANIE
print("\n" + "=" * 80)
print("📊 PODSUMOWANIE")
print("=" * 80)

if successes:
    print(f"\n✅ DZIAŁA DOBRZE ({len(successes)}):")
    for s in successes:
        print(f"   {s}")

if warnings:
    print(f"\n⚠️  OSTRZEŻENIA ({len(warnings)}):")
    for w in warnings:
        print(f"   {w}")

if issues:
    print(f"\n❌ PROBLEMY DO NAPRAWY ({len(issues)}):")
    for i in issues:
        print(f"   {i}")

# Ocena
print("\n" + "=" * 80)
score = len(successes) - len(issues) - (len(warnings) * 0.5)
max_score = len(successes) + len(issues) + len(warnings)

if max_score > 0:
    percentage = (score / max_score) * 100
    print(f"📈 OCENA SEO: {percentage:.0f}%")
    
    if percentage >= 80:
        print("🎉 ŚWIETNIE! Strona jest dobrze zoptymalizowana")
    elif percentage >= 60:
        print("👍 DOBRZE! Popraw kilka rzeczy aby było idealnie")
    else:
        print("⚠️  WYMAGA POPRAWY! Zobacz problemy powyżej")

print("\n" + "=" * 80)
print("📋 NASTĘPNE KROKI:")
print("=" * 80)
print("""
1. Napraw wszystkie ❌ problemy powyżej
2. Rozważ poprawę ⚠️  ostrzeżeń
3. Dodaj stronę do Google Search Console:
   https://search.google.com/search-console/
4. Zgłoś sitemap w GSC: https://manualdonkey.com/sitemap.xml
5. Sprawdź po 7-14 dniach czy Google indeksuje stronę:
   site:manualdonkey.com
""")
