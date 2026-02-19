"""
Add image support to products and create static images folder
"""
import os
from database.models import get_engine
from sqlalchemy import text

def setup_images():
    """Add image_url field to products table and create images folder"""
    
    # Create static/images folder
    images_dir = "static/images/products"
    os.makedirs(images_dir, exist_ok=True)
    print(f"✅ Created images directory: {images_dir}")
    
    # Add image_url column to products table
    engine = get_engine()
    
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR(500)"))
            conn.commit()
            print("✅ Successfully added image_url column to products table")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  Column image_url already exists")
            else:
                print(f"❌ Error adding image_url column: {e}")
    
    # Create placeholder images (you can replace with real images)
    placeholder_info = """
📁 static/images/products/
   
Żeby dodać zdjęcia produktów:

1. Wgraj pliki zdjęć do folderu static/images/products/
   Przykładowe nazwy:
   - samsung-galaxy-s21.jpg
   - ford-f150-2012.jpg
   - bosch-waw28560pl.jpg
   
2. W pliku CSV dodaj kolumnę 'image_url' z ścieżkami:
   title,description,price,category,brand,model,image_url
   "Samsung Galaxy S21","Instrukcja...",29.99,Electronics,Samsung,Galaxy S21,/static/images/products/samsung-galaxy-s21.jpg
   
3. Uruchom ponownie import_csv.py
   
Alternatywnie możesz używać zewnętrznych URL:
   image_url: https://example.com/image.jpg

Jeśli image_url jest puste, będzie wyświetlany domyślny placeholder.
"""
    
    with open(f"{images_dir}/README.txt", "w", encoding="utf-8") as f:
        f.write(placeholder_info)
    
    print("✅ Created README.txt with instructions")
    print("\n" + "="*50)
    print("INSTRUKCJE:")
    print(placeholder_info)

if __name__ == "__main__":
    setup_images()