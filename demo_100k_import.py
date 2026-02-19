"""
DEMO MASOWEGO IMPORTU 100K PRODUKTÓW
Pokazuje jak użyć systemu do importu dużych ilości danych
"""
import sys
import os
from pathlib import Path

# Dodaj folder projektu do sys.path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from bulk_import_products import ProductImporter
from csv_mass_processor import CSVMassProcessor
from product_enhancer import ProductEnhancer

def demo_100k_import():
    """Demonstracja importu 100k produktów"""
    
    print("🚀 DEMO: IMPORT 100K PRODUKTÓW")
    print("="*50)
    
    # 1. Stwórz przykładowy CSV
    print("\n📋 KROK 1: Tworzenie przykładowego pliku CSV")
    processor = CSVMassProcessor()
    template_file = processor.prepare_csv_template("demo_products.csv")
    
    # 2. Rozszerz szablon do większej liczby produktów
    print("\n📈 KROK 2: Rozszerzam szablon do 1000 produktów (demo)")
    create_large_sample(template_file, "large_demo.csv", 1000)
    
    # 3. Analizuj strukturę
    print("\n🔍 KROK 3: Analizuję strukturę pliku")
    processor.analyze_csv_structure("large_demo.csv")
    processor.estimate_processing_time("large_demo.csv")
    
    # 4. Przetworz plik
    print("\n⚡ KROK 4: Przetwarzam produkty")
    processor.process_large_csv("large_demo.csv")
    
    # 5. Połącz przetworzone dane
    print("\n🔗 KROK 5: Łączę przetworzone dane")
    final_file = processor.merge_processed_chunks()
    
    # 6. Import do bazy danych
    print("\n💾 KROK 6: Import do bazy danych")
    importer = ProductImporter()
    success = importer.import_from_csv(final_file)
    
    if success:
        print("\n🎉 DEMO ZAKOŃCZONE SUKCESEM!")
        print("💡 Teraz możesz:")
        print("   1. Sprawdzić produkty na stronie głównej")
        print("   2. Przetestować wyszukiwanie")
        print("   3. Zobaczyć kategoryzację w panelu admina")
    else:
        print("\n❌ Demo nie powiódło się")

def create_large_sample(template_file, output_file, count):
    """Tworzy większy plik przykładowy na podstawie szablonu"""
    import pandas as pd
    import random
    
    # Wczytaj szablon
    template_df = pd.read_csv(template_file)
    
    # Dane do rozszerzenia
    brands = {
        'motorcycles': ['Yamaha', 'Honda', 'Kawasaki', 'Suzuki', 'Ducati', 'BMW', 'KTM', 'Harley-Davidson'],
        'automotive': ['Toyota', 'Ford', 'BMW', 'Mercedes', 'Audi', 'Volkswagen', 'Honda', 'Nissan'],
        'electronics': ['Samsung', 'Apple', 'Sony', 'LG', 'Panasonic', 'Canon', 'Nikon', 'Dell'],
        'tools': ['DeWalt', 'Makita', 'Bosch', 'Milwaukee', 'Black+Decker', 'Craftsman'],
        'marine': ['Yamaha', 'Mercury', 'Honda', 'Suzuki', 'Evinrude']
    }
    
    models = {
        'Yamaha': ['YFZ450R', 'YZ250F', 'MT-07', 'MT-09', 'R1', 'R6', 'Tenere 700', 'FZ-09'],
        'Honda': ['CBR600RR', 'CBR1000RR', 'CRF450R', 'Africa Twin', 'Civic', 'Accord', 'CR-V'],
        'Kawasaki': ['Ninja 650', 'Versys 650', 'Z900', 'KX450F', 'Vulcan S'],
        'Toyota': ['Camry', 'Corolla', 'Prius', 'RAV4', 'Highlander', 'Tacoma'],
        'Samsung': ['Galaxy S21', 'Galaxy Note', 'Galaxy Tab', 'QLED TV', 'SSD 980'],
        'DeWalt': ['DCS371B', 'DCD771C2', 'DWE575SB', 'DCF887B']
    }
    
    years = ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2018-2022', '2020-2024']
    
    # Generuj produkty
    products = []
    
    for i in range(count):
        # Wybierz losową kategorię i brand
        category = random.choice(list(brands.keys()))
        brand = random.choice(brands[category])
        
        # Wybierz model
        if brand in models:
            model = random.choice(models[brand])
        else:
            model = f"Model{random.randint(100, 999)}"
        
        # Stwórz tytuł
        year = random.choice(years)
        title = f"Manual for {brand} {model} {year}"
        
        products.append({
            'title': title,
            'brand': brand,
            'model': model,
            'year': year,
            'category': '',  # Zostanie automatycznie wypełnione
            'price': '',     # Zostanie automatycznie wypełnione
            'description': '' # Zostanie automatycznie wypełnione
        })
    
    # Stwórz DataFrame i zapisz
    df = pd.DataFrame(products)
    df.to_csv(output_file, index=False)
    
    print(f"✅ Utworzono {count} przykładowych produktów w: {output_file}")

def show_import_guide():
    """Pokazuje przewodnik po imporcie"""
    guide = """
🎯 PRZEWODNIK PO MASOWYM IMPORCIE
================================

📁 1. PRZYGOTOWANIE DANYCH:
   • Plik CSV z kolumnami: title, brand, model, year
   • Kodowanie UTF-8
   • Separator: przecinek
   
📊 2. STRUKTURA PLIKU:
   title,brand,model,year
   "Manual for Yamaha YFZ450R 2020-2023",Yamaha,YFZ450R,2020-2023
   "Honda CBR600RR Service Guide 2013-2019",Honda,CBR600RR,2013-2019
   
🤖 3. AUTOMATYCZNA KATEGORYZACJA:
   • Yamaha YFZ → motorcycles
   • Toyota Camry → automotive
   • Samsung Galaxy → electronics
   • DeWalt DCS371B → tools
   
💰 4. INTELIGENTNE CENY:
   • Premium brands: $25-45
   • Standard brands: $15-25
   • Budget brands: $8-18
   • Based on category and brand reputation
   
📝 5. GENEROWANIE OPISÓW:
   • Professional descriptions
   • Category-specific features
   • Brand and model highlights
   
⚡ 6. WYDAJNOŚĆ:
   • 100 produktów na batch
   • ~1000 produktów na sekundę
   • Progress tracking via API
   • Error handling and recovery
   
🔧 7. KOMENDY:
   python bulk_import_products.py          # Demo 10 produktów
   python csv_mass_processor.py            # Przetwarzanie dużych plików
   python product_enhancer.py              # Zaawansowane funkcje
   python demo_100k_import.py              # Ten demo
   
🌐 8. PANEL ADMINA:
   • /admin/import-monitor - Live tracking
   • Real-time progress
   • Error monitoring
   • Start/stop controls
   
💡 9. BEST PRACTICES:
   • Testuj na małych plikach najpierw
   • Sprawdź kategoryzację
   • Monitoruj błędy
   • Rób backup bazy danych przed importem
    """
    print(guide)

if __name__ == "__main__":
    print("🎛️  MENU MASOWEGO IMPORTU")
    print("1. Uruchom demo 1000 produktów")
    print("2. Pokaż przewodnik")
    print("3. Stwórz szablon CSV")
    
    choice = input("\nWybierz opcję (1-3): ").strip()
    
    if choice == "1":
        demo_100k_import()
    elif choice == "2":
        show_import_guide()
    elif choice == "3":
        processor = CSVMassProcessor()
        processor.prepare_csv_template("products_ready_to_fill.csv")
        print("\n✅ Szablon gotowy! Wypełnij products_ready_to_fill.csv swoimi danymi")
    else:
        print("❌ Nieprawidłowa opcja")