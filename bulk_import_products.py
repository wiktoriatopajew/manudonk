"""
BULK PRODUCT IMPORT SYSTEM
Importuje tysiące produktów z automatyczną kategoryzacją, opisami i cenami
"""
import pandas as pd
import re
from database.models import get_session, Product, Base
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

class ProductImporter:
    def __init__(self):
        self.session = get_session()
        
        # Mapowanie brandów na kategorie
        self.brand_categories = {
            # Motorcycles
            'yamaha': 'motorcycles', 'kawasaki': 'motorcycles', 'honda': 'motorcycles',
            'suzuki': 'motorcycles', 'ducati': 'motorcycles', 'harley-davidson': 'motorcycles',
            'bmw': 'motorcycles', 'ktm': 'motorcycles', 'aprilia': 'motorcycles',
            'triumph': 'motorcycles', 'indian': 'motorcycles', 'victory': 'motorcycles',
            
            # Cars
            'toyota': 'automotive', 'ford': 'automotive', 'chevrolet': 'automotive',
            'volkswagen': 'automotive', 'audi': 'automotive', 'mercedes': 'automotive',
            'bmw': 'automotive', 'nissan': 'automotive', 'hyundai': 'automotive',
            'kia': 'automotive', 'mazda': 'automotive', 'subaru': 'automotive',
            
            # Electronics
            'samsung': 'electronics', 'apple': 'electronics', 'sony': 'electronics',
            'lg': 'electronics', 'panasonic': 'electronics', 'philips': 'electronics',
            'canon': 'electronics', 'nikon': 'electronics', 'epson': 'electronics',
            
            # Home Appliances
            'whirlpool': 'home-appliances', 'ge': 'home-appliances', 'frigidaire': 'home-appliances',
            'kenmore': 'home-appliances', 'maytag': 'home-appliances', 'bosch': 'home-appliances',
            
            # Power Tools
            'dewalt': 'tools', 'makita': 'tools', 'milwaukee': 'tools',
            'bosch': 'tools', 'craftsman': 'tools', 'ryobi': 'tools',
        }
        
        # Modele motocykli (dla lepszej klasyfikacji)
        self.motorcycle_models = {
            'yfz', 'raptor', 'banshee', 'warrior', 'blaster',  # Yamaha ATVs
            'versys', 'ninja', 'klr', 'z', 'zx', 'er',        # Kawasaki
            'cbr', 'crf', 'cb', 'vtx', 'shadow', 'goldwing',  # Honda
            'gsxr', 'sv', 'dr', 'rmz', 'ltz', 'kingquad',     # Suzuki
        }
        
        # Ceny na podstawie kategorii i typu
        self.category_prices = {
            'motorcycles': {'min': 15, 'max': 45, 'default': 25},
            'automotive': {'min': 12, 'max': 35, 'default': 20},
            'electronics': {'min': 8, 'max': 25, 'default': 15},
            'home-appliances': {'min': 10, 'max': 30, 'default': 18},
            'tools': {'min': 12, 'max': 28, 'default': 18},
            'other': {'min': 8, 'max': 20, 'default': 12}
        }

    def normalize_brand(self, brand):
        """Normalizuje nazwę brandu"""
        if not brand:
            return 'Unknown'
        
        brand = brand.lower().strip()
        
        # Mapowanie często mylonych nazw
        brand_aliases = {
            'harley davidson': 'harley-davidson',
            'h-d': 'harley-davidson',
            'bimmer': 'bmw',
            'merc': 'mercedes',
            'vw': 'volkswagen',
            'chevy': 'chevrolet',
        }
        
        return brand_aliases.get(brand, brand)

    def smart_categorize(self, brand, model, title):
        """Inteligentnie przypisuje kategorię na podstawie brand + model"""
        brand = self.normalize_brand(brand)
        model_lower = model.lower() if model else ''
        title_lower = title.lower() if title else ''
        
        # Sprawdź brand mapping
        if brand in self.brand_categories:
            category = self.brand_categories[brand]
            
            # Dla brandów które mają produkty w różnych kategoriach (np. Honda - auta i motocykle)
            if brand in ['honda', 'yamaha', 'suzuki', 'kawasaki']:
                # Sprawdź model czy to motocykl
                for moto_model in self.motorcycle_models:
                    if moto_model in model_lower or moto_model in title_lower:
                        return 'motorcycles'
                
                # Sprawdź słowa kluczowe w tytule
                motorcycle_keywords = ['atv', 'quad', 'dirt bike', 'motorcycle', 'bike', 'scooter']
                car_keywords = ['car', 'sedan', 'suv', 'truck', 'van', 'accord', 'civic', 'camry']
                
                for keyword in motorcycle_keywords:
                    if keyword in title_lower:
                        return 'motorcycles'
                        
                for keyword in car_keywords:
                    if keyword in title_lower:
                        return 'automotive'
                        
            return category
        
        # Fallback na słowa kluczowe w tytule
        category_keywords = {
            'motorcycles': ['motorcycle', 'bike', 'atv', 'quad', 'scooter', 'dirt bike', 'sport bike'],
            'automotive': ['car', 'truck', 'van', 'suv', 'sedan', 'vehicle', 'auto'],
            'electronics': ['tv', 'phone', 'camera', 'laptop', 'computer', 'tablet', 'radio'],
            'home-appliances': ['refrigerator', 'washer', 'dryer', 'dishwasher', 'microwave', 'oven'],
            'tools': ['drill', 'saw', 'grinder', 'tool', 'wrench', 'hammer']
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category
                    
        return 'other'

    def generate_price(self, category, brand, model):
        """Generuje realistyczną cenę na podstawie kategorii i brandu"""
        price_config = self.category_prices.get(category, self.category_prices['other'])
        
        base_price = price_config['default']
        
        # Premium brands get higher prices
        premium_brands = ['bmw', 'mercedes', 'audi', 'ducati', 'apple', 'sony']
        if brand.lower() in premium_brands:
            base_price = price_config['max']
        
        # Budget brands get lower prices
        budget_brands = ['hyundai', 'kia', 'yamaha']
        if brand.lower() in budget_brands:
            base_price = price_config['min']
            
        # Add some variation based on model length (longer model = more complex = higher price)
        if model and len(model) > 6:
            base_price += 2
            
        return min(max(base_price, price_config['min']), price_config['max'])

    def generate_description(self, brand, model, category):
        """Generuje profesjonalny opis produktu"""
        category_descriptions = {
            'motorcycles': f"Official user manual for {brand} {model} motorcycle. Complete maintenance guide including engine specifications, electrical diagrams, troubleshooting procedures, and safety instructions. Essential for proper operation and maintenance.",
            
            'automotive': f"Comprehensive service manual for {brand} {model} vehicle. Detailed repair procedures, wiring diagrams, maintenance schedules, and technical specifications. Professional-grade documentation for mechanics and owners.",
            
            'electronics': f"Complete user guide for {brand} {model}. Step-by-step setup instructions, feature explanations, troubleshooting tips, and safety information. Get the most out of your device with this official manual.",
            
            'home-appliances': f"Official operation manual for {brand} {model}. Installation guide, operating instructions, maintenance procedures, and warranty information. Keep your appliance running efficiently.",
            
            'tools': f"Professional manual for {brand} {model} tool. Safety instructions, operating procedures, maintenance guidelines, and parts diagrams. Essential for safe and effective use.",
            
            'other': f"User manual for {brand} {model}. Complete instructions, specifications, and maintenance information. Official documentation for proper operation."
        }
        
        base_description = category_descriptions.get(category, category_descriptions['other'])
        
        # Add category-specific features
        feature_additions = {
            'motorcycles': " Includes engine tuning, brake system maintenance, and seasonal storage tips.",
            'automotive': " Features diagnostic procedures, fluid specifications, and recall information.",
            'electronics': " Contains connectivity guides, software updates, and accessories information.",
            'home-appliances': " Covers energy efficiency tips, cleaning procedures, and common repairs.",
            'tools': " Includes blade/bit specifications, proper handling techniques, and maintenance schedules."
        }
        
        description = base_description + feature_additions.get(category, "")
        description += f" High-quality PDF format, immediately downloadable after purchase. Compatible with all devices."
        
        return description

    def generate_slug(self, brand, model):
        """Generuje SEO-friendly slug"""
        slug = f"{brand}-{model}".lower()
        # Remove special characters and replace spaces with hyphens
        slug = re.sub(r'[^a-z0-9\-]', '', slug.replace(' ', '-'))
        # Remove multiple hyphens
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug

    def import_from_csv(self, csv_file):
        """Importuje produkty z pliku CSV"""
        try:
            df = pd.read_csv(csv_file)
            
            print(f"📊 Wczytano {len(df)} produktów z {csv_file}")
            
            # Wymagane kolumny
            required_columns = ['title', 'brand', 'model']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"❌ Brak wymaganych kolumn: {missing_columns}")
                return False
                
            imported_count = 0
            skipped_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Wyczyść dane
                    brand = self.normalize_brand(row.get('brand', ''))
                    model = str(row.get('model', '')).strip()
                    title = str(row.get('title', '')).strip()
                    
                    if not title or not brand or not model:
                        skipped_count += 1
                        continue
                    
                    # Sprawdź czy produkt już istnieje
                    slug = self.generate_slug(brand, model)
                    existing = self.session.query(Product).filter(Product.slug == slug).first()
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Inteligentna kategoryzacja
                    category = self.smart_categorize(brand, model, title)
                    
                    # Generuj cenę
                    price = self.generate_price(category, brand, model)
                    
                    # Generuj opis
                    description = self.generate_description(brand, model, category)
                    
                    # Użyj dostarczonego image_url lub None
                    image_url = row.get('image_url', None)
                    if pd.isna(image_url):
                        image_url = None
                    
                    # Stwórz produkt
                    product = Product(
                        title=title,
                        brand=brand,
                        model=model,
                        category=category,
                        description=description,
                        price=price,
                        slug=slug,
                        image_url=image_url
                    )
                    
                    self.session.add(product)
                    imported_count += 1
                    
                    # Commit co 100 produktów
                    if imported_count % 100 == 0:
                        self.session.commit()
                        print(f"✅ Zaimportowano {imported_count} produktów...")
                        
                except Exception as e:
                    print(f"❌ Błąd dla wiersza {index}: {e}")
                    skipped_count += 1
                    continue
            
            # Final commit
            self.session.commit()
            print(f"🎉 Import zakończony!")
            print(f"   ✅ Zaimportowano: {imported_count}")
            print(f"   ⏭️  Pominięto: {skipped_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas importu: {e}")
            self.session.rollback()
            return False
        finally:
            self.session.close()
    
    def import_from_csv_with_progress(self, csv_file):
        """Importuje produkty z pliku CSV z raportowaniem postępu dla API"""
        # Import global status from api_routes if available
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            # This will work when called from the API
            api_routes = sys.modules.get('api_routes')
            if api_routes and hasattr(api_routes, 'import_status'):
                global_status = api_routes.import_status
            else:
                global_status = None
        except:
            global_status = None
            
        try:
            df = pd.read_csv(csv_file)
            
            print(f"📊 Wczytano {len(df)} produktów z {csv_file}")
            
            # Wymagane kolumny
            required_columns = ['title', 'brand', 'model']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                error_msg = f"Brak wymaganych kolumn: {missing_columns}"
                print(f"❌ {error_msg}")
                if global_status:
                    global_status["errors"].append({"time": pd.Timestamp.now().isoformat(), "error": error_msg})
                return False
                
            total_products = len(df)
            imported_count = 0
            skipped_count = 0
            
            if global_status:
                global_status.update({
                    "total": total_products,
                    "last_update": pd.Timestamp.now().isoformat()
                })
            
            for index, row in df.iterrows():
                try:
                    # Wyczyść dane
                    brand = self.normalize_brand(row.get('brand', ''))
                    model = str(row.get('model', '')).strip()
                    title = str(row.get('title', '')).strip()
                    
                    if not title or not brand or not model:
                        skipped_count += 1
                        continue
                    
                    # Sprawdź czy produkt już istnieje
                    slug = self.generate_slug(brand, model)
                    existing = self.session.query(Product).filter(Product.slug == slug).first()
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Inteligentna kategoryzacja
                    category = self.smart_categorize(brand, model, title)
                    
                    # Generuj cenę
                    price = self.generate_price(category, brand, model)
                    
                    # Generuj opis
                    description = self.generate_description(brand, model, category)
                    
                    # Użyj dostarczonego image_url lub None
                    image_url = row.get('image_url', None)
                    if pd.isna(image_url):
                        image_url = None
                    
                    # Stwórz produkt
                    product = Product(
                        title=title,
                        brand=brand,
                        model=model,
                        category=category,
                        description=description,
                        price=price,
                        slug=slug,
                        image_url=image_url
                    )
                    
                    self.session.add(product)
                    imported_count += 1
                    
                    # Update progress
                    if global_status:
                        progress_percent = int((imported_count / total_products) * 100)
                        current_batch = (imported_count // 100) + 1
                        global_status.update({
                            "progress": imported_count,
                            "percentage": progress_percent,
                            "current_batch": current_batch,
                            "last_update": pd.Timestamp.now().isoformat()
                        })
                    
                    # Commit co 100 produktów
                    if imported_count % 100 == 0:
                        self.session.commit()
                        print(f"✅ Zaimportowano {imported_count} produktów...")
                        
                except Exception as e:
                    error_msg = f"Błąd dla wiersza {index}: {e}"
                    print(f"❌ {error_msg}")
                    if global_status:
                        global_status["errors"].append({"time": pd.Timestamp.now().isoformat(), "error": error_msg})
                    skipped_count += 1
                    continue
            
            # Final commit
            self.session.commit()
            print(f"🎉 Import zakończony!")
            print(f"   ✅ Zaimportowano: {imported_count}")
            print(f"   ⏭️  Pominięto: {skipped_count}")
            
            if global_status:
                global_status.update({
                    "progress": imported_count,
                    "percentage": 100,
                    "active": False,
                    "last_update": pd.Timestamp.now().isoformat()
                })
            
            return True
            
        except Exception as e:
            error_msg = f"Błąd podczas importu: {e}"
            print(f"❌ {error_msg}")
            self.session.rollback()
            if global_status:
                global_status["errors"].append({"time": pd.Timestamp.now().isoformat(), "error": error_msg})
                global_status.update({
                    "active": False,
                    "last_update": pd.Timestamp.now().isoformat()
                })
            return False
        finally:
            self.session.close()

    def create_sample_csv(self, filename="sample_products.csv"):
        """Tworzy przykładowy plik CSV z produktami"""
        sample_data = [
            {"title": "Yamaha YFZ 450R ATV Service Manual", "brand": "Yamaha", "model": "YFZ450R"},
            {"title": "Kawasaki Versys 650 Motorcycle Manual", "brand": "Kawasaki", "model": "Versys 650"},
            {"title": "Honda Civic 2020 Repair Guide", "brand": "Honda", "model": "Civic 2020"},
            {"title": "Samsung Galaxy S21 User Manual", "brand": "Samsung", "model": "Galaxy S21"},
            {"title": "DeWalt 20V Drill Instruction Manual", "brand": "DeWalt", "model": "DCD777C2"},
            {"title": "Whirlpool Washer WTW5000DW Manual", "brand": "Whirlpool", "model": "WTW5000DW"},
            {"title": "BMW R1250GS Adventure Manual", "brand": "BMW", "model": "R1250GS"},
            {"title": "Toyota Camry 2022 Service Manual", "brand": "Toyota", "model": "Camry 2022"},
            {"title": "Apple iPhone 13 Pro User Guide", "brand": "Apple", "model": "iPhone 13 Pro"},
            {"title": "Suzuki LTZ 400 ATV Repair Manual", "brand": "Suzuki", "model": "LTZ 400"},
        ]
        
        df = pd.DataFrame(sample_data)
        df.to_csv(filename, index=False)
        print(f"📄 Utworzono przykładowy plik: {filename}")
        return filename

# Użycie:
if __name__ == "__main__":
    importer = ProductImporter()
    
    # Stwórz przykładowy plik
    sample_file = importer.create_sample_csv()
    
    # Importuj z CSV
    print("\n🚀 Rozpoczynam import...")
    success = importer.import_from_csv(sample_file)
    
    if success:
        print("\n✅ Import zakończony pomyślnie!")
    else:
        print("\n❌ Import nieudany!")