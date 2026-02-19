"""
CSV PROCESSOR - Przygotowuje i przetwarza masowe pliki CSV
"""
import pandas as pd
import numpy as np
from pathlib import Path
import time

class CSVMassProcessor:
    def __init__(self):
        self.chunk_size = 10000  # Przetwarzaj po 10k produktów naraz
        self.required_columns = ['title', 'brand', 'model']
        
    def prepare_csv_template(self, filename="products_template.csv"):
        """Tworzy szablon CSV do wypełnienia"""
        template_data = {
            'title': [
                'Manual for Yamaha YFZ450R 2009-2013',
                'Honda CBR600RR Service Manual 2013-2019',
                'Toyota Camry Repair Guide 2018-2022',
                'Samsung Galaxy S21 User Manual',
                'DeWalt DCS371B Instruction Manual'
            ],
            'brand': ['Yamaha', 'Honda', 'Toyota', 'Samsung', 'DeWalt'],
            'model': ['YFZ450R', 'CBR600RR', 'Camry', 'Galaxy S21', 'DCS371B'],
            'year': ['2009-2013', '2013-2019', '2018-2022', '2021', '2020'],
            'category': ['', '', '', '', ''],  # Zostanie automatycznie wypełnione
            'price': ['', '', '', '', ''],     # Zostanie automatycznie wypełnione
            'description': ['', '', '', '', ''] # Zostanie automatycznie wypełnione
        }
        
        df = pd.DataFrame(template_data)
        df.to_csv(filename, index=False)
        
        print(f"📋 Szablon utworzony: {filename}")
        print("💡 Wypełnij kolumny: title, brand, model, year")
        print("🤖 Reszta zostanie automatycznie wygenerowana")
        
        return filename

    def analyze_csv_structure(self, csv_file):
        """Analizuje strukturę pliku CSV"""
        try:
            # Sprawdź pierwsze wiersze
            sample = pd.read_csv(csv_file, nrows=10)
            
            print(f"📊 ANALIZA PLIKU: {csv_file}")
            print("="*50)
            print(f"📄 Kolumny: {list(sample.columns)}")
            print(f"📈 Przykładowe dane:")
            print(sample.head(3))
            
            # Sprawdź pełny rozmiar
            with open(csv_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for line in f) - 1  # -1 dla nagłówka
            
            print(f"📊 Rozmiar: {line_count:,} produktów")
            
            # Walidacja kolumn
            missing_cols = set(self.required_columns) - set(sample.columns)
            if missing_cols:
                print(f"❌ Brakujące kolumny: {missing_cols}")
                return False
            
            print("✅ Struktura pliku poprawna")
            return True
            
        except Exception as e:
            print(f"❌ Błąd analizy: {e}")
            return False

    def estimate_processing_time(self, csv_file):
        """Szacuje czas przetwarzania"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for line in f) - 1
            
            # Na podstawie testów: ~1000 produktów na sekundę
            estimated_seconds = line_count / 1000
            
            if estimated_seconds < 60:
                time_str = f"{estimated_seconds:.1f} sekund"
            elif estimated_seconds < 3600:
                time_str = f"{estimated_seconds/60:.1f} minut"
            else:
                time_str = f"{estimated_seconds/3600:.1f} godzin"
            
            print(f"⏱️  Szacowany czas: {time_str}")
            print(f"📦 Będzie przetwarzane po {self.chunk_size:,} produktów")
            
            return estimated_seconds
            
        except Exception as e:
            print(f"❌ Błąd szacowania: {e}")
            return 0

    def process_large_csv(self, csv_file, output_dir="processed_data"):
        """Przetwarza duży CSV porcjami"""
        Path(output_dir).mkdir(exist_ok=True)
        
        print(f"🚀 PRZETWARZANIE: {csv_file}")
        print("="*50)
        
        try:
            # Najpierw analizuj
            if not self.analyze_csv_structure(csv_file):
                return False
            
            self.estimate_processing_time(csv_file)
            
            # Przetwarzaj porcjami
            chunk_results = []
            total_processed = 0
            
            for chunk_num, chunk in enumerate(pd.read_csv(csv_file, chunksize=self.chunk_size)):
                print(f"📦 Przetwarzam porcję {chunk_num + 1} ({len(chunk)} produktów)...")
                
                # Tutaj można dodać przetwarzanie każdej porcji
                # np. kategoryzację, generowanie cen, opisów
                
                processed_chunk = self.process_chunk(chunk, chunk_num)
                
                # Zapisz przetworzoną porcję
                output_file = f"{output_dir}/processed_chunk_{chunk_num:04d}.csv"
                processed_chunk.to_csv(output_file, index=False)
                
                chunk_results.append({
                    'chunk': chunk_num,
                    'products': len(processed_chunk),
                    'file': output_file
                })
                
                total_processed += len(processed_chunk)
                
                if chunk_num % 10 == 0:  # Progress co 10 porcji
                    print(f"   ✅ Przetworzono już {total_processed:,} produktów...")
            
            # Podsumowanie
            print(f"\n🎉 UKOŃCZONO!")
            print(f"📊 Całkowicie przetworzono: {total_processed:,} produktów")
            print(f"📁 Wyniki w folderze: {output_dir}/")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd przetwarzania: {e}")
            return False

    def process_chunk(self, chunk_df, chunk_num):
        """Przetwarza pojedynczą porcję danych"""
        from product_enhancer import ProductEnhancer
        
        enhancer = ProductEnhancer()
        
        # Waliduj i oczyść
        chunk_df = enhancer.validate_and_clean_data(chunk_df)
        
        # Dodaj smart kategoryzację i pricing
        processed_rows = []
        
        for index, row in chunk_df.iterrows():
            brand = enhancer.normalize_brand(row.get('brand', ''))
            model = str(row.get('model', '')).strip()
            title = str(row.get('title', '')).strip()
            
            # Smart categorization
            category = enhancer.smart_categorize(brand, model, title)
            price = enhancer.generate_price(category, brand, model)
            description = enhancer.generate_description(brand, model, category)
            
            # Dodaj wygenerowane dane
            row['category'] = category
            row['price'] = price
            row['description'] = description
            row['slug'] = enhancer.create_slug(title)
            
            processed_rows.append(row)
        
        return pd.DataFrame(processed_rows)

    def merge_processed_chunks(self, processed_dir="processed_data", output_file="final_products.csv"):
        """Łączy wszystkie przetworzone porcje w jeden plik"""
        print(f"🔗 Łączę przetworzone porcje...")
        
        chunk_files = list(Path(processed_dir).glob("processed_chunk_*.csv"))
        chunk_files.sort()
        
        if not chunk_files:
            print("❌ Nie znaleziono przetworzeonych porcji")
            return False
        
        all_chunks = []
        total_products = 0
        
        for chunk_file in chunk_files:
            chunk = pd.read_csv(chunk_file)
            all_chunks.append(chunk)
            total_products += len(chunk)
            
            print(f"   📦 {chunk_file.name}: {len(chunk)} produktów")
        
        # Połącz wszystko
        final_df = pd.concat(all_chunks, ignore_index=True)
        final_df.to_csv(output_file, index=False)
        
        print(f"\n✅ Połączono {total_products:,} produktów")
        print(f"📁 Końcowy plik: {output_file}")
        
        return output_file

def main():
    processor = CSVMassProcessor()
    
    print("🏭 CSV MASS PROCESSOR")
    print("="*30)
    print("1. Stwórz szablon CSV")
    print("2. Przetworz duży plik CSV")
    print("3. Połącz przetworzone porcje")
    
    choice = input("\nWybierz opcję (1-3): ").strip()
    
    if choice == "1":
        template = processor.prepare_csv_template()
        print(f"\n✅ Szablon gotowy: {template}")
        print("💡 Wypełnij go swoimi danymi i uruchom opcję 2")
        
    elif choice == "2":
        csv_file = input("Podaj ścieżkę do pliku CSV: ").strip()
        if Path(csv_file).exists():
            processor.process_large_csv(csv_file)
        else:
            print(f"❌ Plik nie istnieje: {csv_file}")
            
    elif choice == "3":
        output = processor.merge_processed_chunks()
        if output:
            print(f"\n🎉 Gotowe! Możesz teraz zaimportować: {output}")

if __name__ == "__main__":
    main()