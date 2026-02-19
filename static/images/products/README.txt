
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
