"""
ADVANCED PRODUCT DATA ENHANCER
Wykorzystuje AI/API do generowania opisów i automatycznej kategoryzacji
"""
import requests
import json
import time
from bulk_import_products import ProductImporter

class ProductEnhancer(ProductImporter):
    def __init__(self):
        super().__init__()
        self.use_ai_descriptions = False  # Zmień na True jeśli masz dostęp do OpenAI API
        
    def enhance_with_ai_description(self, brand, model, category):
        """Generuje opis używając AI (opcjonalne - wymaga OpenAI API)"""
        if not self.use_ai_descriptions:
            return self.generate_description(brand, model, category)
            
        try:
            # Przykład z OpenAI API (wymaga klucza API)
            prompt = f"""
            Create a professional product description for a {brand} {model} manual in the {category} category.
            The description should be 2-3 sentences, mention key features, and encourage purchase.
            Focus on the manual's value for maintenance and operation.
            """
            
            # Tu byłoby wywołanie do OpenAI API
            # response = openai.Completion.create(...)
            
            # Na razie użyj standardowego generatora
            return self.generate_description(brand, model, category)
            
        except Exception as e:
            print(f"AI description failed for {brand} {model}, using standard: {e}")
            return self.generate_description(brand, model, category)

    def get_realistic_pricing_data(self):
        """Pobiera aktualne ceny z zewnętrznych źródeł (opcjonalne)"""
        # Tu można by dodać integrację z:
        # - eBay API dla cen podręczników
        # - Amazon API
        # - Własna baza danych cen
        
        # Na razie używamy statycznych zasad cenowych
        return self.category_prices

    def batch_process_categories(self, products_df):
        """Masowo przetwarza kategorie dla wszystkich produktów"""
        print("🔄 Przeprowadzam analizę kategorii...")
        
        categorized = []
        category_stats = {}
        
        for index, row in products_df.iterrows():
            brand = self.normalize_brand(row.get('brand', ''))
            model = str(row.get('model', '')).strip()
            title = str(row.get('title', '')).strip()
            
            category = self.smart_categorize(brand, model, title)
            
            # Statystyki
            category_stats[category] = category_stats.get(category, 0) + 1
            
            row['suggested_category'] = category
            row['suggested_price'] = self.generate_price(category, brand, model)
            row['enhanced_description'] = self.enhance_with_ai_description(brand, model, category)
            
            categorized.append(row)
            
            if index % 1000 == 0:
                print(f"   Przeanalizowano {index} produktów...")
        
        print("\n📊 Statystyki kategoryzacji:")
        for category, count in sorted(category_stats.items()):
            print(f"   {category}: {count} produktów")
            
        return categorized

    def validate_and_clean_data(self, products_df):
        """Waliduje i czyści dane przed importem"""
        print("🧹 Czyszczenie danych...")
        
        original_count = len(products_df)
        
        # Usuń duplikaty na podstawie brand + model
        products_df['unique_key'] = products_df['brand'].str.lower() + '_' + products_df['model'].str.lower()
        products_df = products_df.drop_duplicates(subset=['unique_key'])
        
        # Usuń produkty bez wymaganych danych
        products_df = products_df.dropna(subset=['title', 'brand', 'model'])
        
        # Znormalizuj dane
        products_df['brand'] = products_df['brand'].apply(self.normalize_brand)
        products_df['model'] = products_df['model'].str.strip()
        products_df['title'] = products_df['title'].str.strip()
        
        cleaned_count = len(products_df)
        removed_count = original_count - cleaned_count
        
        print(f"   ✅ Oczyszczono dane: {cleaned_count} produktów")
        print(f"   🗑️  Usunięto: {removed_count} duplikatów/niepełnych")
        
        return products_df

    def generate_bulk_import_report(self, results):
        """Generuje raport z importu"""
        report = f"""
        
📋 RAPORT Z IMPORTU MASOWEGO
{'='*50}

📊 PODSUMOWANIE:
• Produkty do importu: {results.get('total', 0)}
• Pomyślnie zaimportowane: {results.get('imported', 0)}
• Pominięte (duplikaty): {results.get('skipped', 0)}
• Błędy: {results.get('errors', 0)}

📈 KATEGORIE:
"""
        
        if 'categories' in results:
            for category, count in results['categories'].items():
                report += f"• {category}: {count} produktów\n"
        
        report += f"""
💰 CENY:
• Średnia cena: ${results.get('avg_price', 0):.2f}
• Najniższa: ${results.get('min_price', 0):.2f}
• Najwyższa: ${results.get('max_price', 0):.2f}

⚡ WYDAJNOŚĆ:
• Czas importu: {results.get('import_time', 0):.1f}s
• Produktów na sekundę: {results.get('products_per_second', 0):.1f}
"""
        
        return report

# Przykład użycia dla masowego importu
def mass_import_example():
    """Przykład masowego importu 100k produktów"""
    
    print("🚀 MASOWY IMPORT PRODUKTÓW")
    print("="*50)
    
    enhancer = ProductEnhancer()
    
    # Tu wczytałbyś prawdziwy plik CSV z 100k produktów
    csv_file = "your_massive_products_file.csv"
    
    print(f"📂 Sprawdzam plik: {csv_file}")
    
    # Na razie stwórz próbkę
    sample_file = enhancer.create_sample_csv("enhanced_sample.csv")
    
    print("\n✨ Uruchamiam zaawansowany import...")
    start_time = time.time()
    
    success = enhancer.import_from_csv(sample_file)
    
    import_time = time.time() - start_time
    
    if success:
        print(f"\n🎉 IMPORT ZAKOŃCZONY w {import_time:.1f}s")
        print("\n💡 NASTĘPNE KROKI:")
        print("1. Przygotuj plik CSV z 100k produktów")
        print("2. Uruchom: python bulk_import_products.py")
        print("3. Sprawdź kategoryzację w panelu admina")
        print("4. Dostosuj ceny jeśli potrzeba")

if __name__ == "__main__":
    mass_import_example()