# Poppler Installation Guide (Windows)

Poppler jest wymagany do konwersji stron PDF na obrazy (dla podglądu).

## Instalacja na Windows

### Opcja 1: Szybka instalacja (Zalecana)

1. Pobierz najnowszą wersję:
   https://github.com/oschwartz10612/poppler-windows/releases/

2. Pobierz plik: `Release-XX.XX.X-X.zip` (najnowsza wersja)

3. Rozpakuj do: `C:\poppler`
   
   Struktura folderów powinna wyglądać:
   ```
   C:\poppler\
   ├── Library\
   │   └── bin\
   │       ├── pdfinfo.exe
   │       ├── pdftoppm.exe
   │       └── ... (inne narzędzia)
   ```

4. Dodaj do PATH:
   
   **Metoda A - PowerShell (Administrator)**:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\poppler\Library\bin", [EnvironmentVariableTarget]::Machine)
   ```
   
   **Metoda B - Ręcznie**:
   - Kliknij prawym na "Ten komputer" > Właściwości
   - Zaawansowane ustawienia systemu
   - Zmienne środowiskowe
   - W sekcji "Zmienne systemowe" znajdź "Path"
   - Edytuj i dodaj: `C:\poppler\Library\bin`
   - Kliknij OK

5. **Zrestartuj terminal/PowerShell**

6. Sprawdź instalację:
   ```powershell
   pdfinfo -v
   ```
   
   Powinno pokazać wersję Poppler.

### Opcja 2: Conda (jeśli używasz Anaconda)

```bash
conda install -c conda-forge poppler
```

## Test

Uruchom w Pythonie:
```python
from pdf2image import convert_from_path

# Jeśli działa, wszystko OK!
```

## Rozwiązywanie problemów

### "poppler not found" po instalacji

1. Sprawdź czy pdfinfo.exe działa w terminalu:
   ```powershell
   pdfinfo -v
   ```

2. Jeśli nie działa, podaj ścieżkę bezpośrednio w kodzie:
   ```python
   images = convert_from_path(
       pdf_path,
       poppler_path=r'C:\poppler\Library\bin'
   )
   ```

3. Upewnij się że zrestartowałeś terminal po dodaniu do PATH

### Alternatywne ścieżki

Jeśli rozpkowałeś gdzie indziej, znajdź folder z plikami .exe:
- pdfinfo.exe
- pdftoppm.exe  
- pdfimages.exe

I użyj tej ścieżki w `poppler_path`.

## Sprawdzenie instalacji

Po poprawnej instalacji ten skrypt powinien działać:

```python
import pdf_manager
manager = pdf_manager.PDFManager()
# Test generowania podglądu
manager.generate_preview_images(Path("test.pdf"), 123)
```
