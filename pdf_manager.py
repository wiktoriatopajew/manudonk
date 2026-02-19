"""
PDF Manager - Download, Preview Generation, and Google Drive Upload
"""
import os
import csv
import requests
from pathlib import Path
import time
from typing import Optional, Dict, List
from pdf2image import convert_from_path
from PIL import Image
import io

# Directories
PDF_STORAGE = Path("storage/pdfs")
PREVIEW_STORAGE = Path("static/images/previews")

# Create directories if they don't exist
PDF_STORAGE.mkdir(parents=True, exist_ok=True)
PREVIEW_STORAGE.mkdir(parents=True, exist_ok=True)


class PDFManager:
    """Manages PDF downloads, previews, and uploads"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_pdf(self, url: str, product_id: int, title: str) -> Optional[Path]:
        """
        Download PDF from URL and save locally
        
        Args:
            url: Direct download URL
            product_id: Unique product ID
            title: Product title for filename
        
        Returns:
            Path to saved PDF or None if failed
        """
        try:
            print(f"📥 Downloading: {title}...")
            
            # Clean filename
            safe_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_filename = safe_filename[:100]  # Limit length
            filename = f"{product_id}_{safe_filename}.pdf"
            filepath = PDF_STORAGE / filename
            
            # Skip if already exists
            if filepath.exists():
                print(f"✅ Already exists: {filename}")
                return filepath
            
            # Download with streaming for large files
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                print(f"⚠️  Warning: Content-Type is {content_type}, not PDF")
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✅ Downloaded: {filename} ({file_size_mb:.2f} MB)")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error downloading {title}: {str(e)}")
            return None
    
    def download_single_pdf(self, product_id: int, title: str, pdf_url: str) -> Optional[Dict]:
        """
        Download a single PDF (used for on-demand downloads after purchase)
        
        Args:
            product_id: Product ID
            title: Product title
            pdf_url: PDF download URL
        
        Returns:
            Dictionary with success status and paths
        """
        try:
            # Download PDF
            pdf_path = self.download_pdf(pdf_url, product_id, title)
            
            if not pdf_path:
                return {
                    'success': False,
                    'error': 'Failed to download PDF'
                }
            
            # Try to generate previews (optional, won't fail if Poppler not installed)
            preview_paths = []
            try:
                preview_paths = self.generate_preview_images(pdf_path, product_id)
            except Exception as e:
                print(f"⚠️  Could not generate previews (Poppler may not be installed): {e}")
            
            return {
                'success': True,
                'pdf_path': str(pdf_path),
                'preview_paths': [str(p) for p in preview_paths]
            }
            
        except Exception as e:
            print(f"❌ Error in download_single_pdf: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_preview_images(self, pdf_path: Path, product_id: int, num_pages: int = 5) -> List[Path]:
        """
        Generate preview images from first N pages of PDF
        
        Args:
            pdf_path: Path to PDF file
            product_id: Product ID for naming
            num_pages: Number of pages to convert (default 5)
        
        Returns:
            List of paths to generated preview images
        """
        try:
            print(f"🖼️  Generating preview for product {product_id}...")
            
            preview_dir = PREVIEW_STORAGE / str(product_id)
            preview_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert PDF pages to images
            # Note: Requires poppler installed
            images = convert_from_path(
                pdf_path,
                first_page=1,
                last_page=num_pages,
                dpi=150  # Good quality but not too large
            )
            
            preview_paths = []
            for i, image in enumerate(images, 1):
                # Resize to reasonable size (max width 800px)
                if image.width > 800:
                    ratio = 800 / image.width
                    new_size = (800, int(image.height * ratio))
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save as JPEG (smaller than PNG)
                preview_path = preview_dir / f"page_{i}.jpg"
                image.save(preview_path, 'JPEG', quality=85, optimize=True)
                preview_paths.append(preview_path)
                print(f"  ✅ Page {i} saved")
            
            print(f"✅ Generated {len(preview_paths)} preview images")
            return preview_paths
            
        except Exception as e:
            print(f"❌ Error generating preview: {str(e)}")
            print("⚠️  Make sure poppler is installed: https://github.com/oschwartz10612/poppler-windows/releases/")
            return []
    
    def process_csv(self, csv_path: str) -> Dict[int, Dict]:
        """
        Process CSV file and download all PDFs
        
        Args:
            csv_path: Path to CSV file
        
        Returns:
            Dictionary with product_id as key and info as value
        """
        results = {}
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                product_id = int(row['ID'])
                title = row['English Title']
                pdf_url = row['Link PDF']
                
                print(f"\n{'='*60}")
                print(f"Processing: {title}")
                print(f"ID: {product_id}")
                
                # Download PDF
                pdf_path = self.download_pdf(pdf_url, product_id, title)
                
                if pdf_path:
                    # Generate preview images
                    preview_paths = self.generate_preview_images(pdf_path, product_id)
                    
                    results[product_id] = {
                        'title': title,
                        'category': row['Category'],
                        'pdf_path': str(pdf_path),
                        'preview_paths': [str(p) for p in preview_paths],
                        'status': 'success'
                    }
                else:
                    results[product_id] = {
                        'title': title,
                        'category': row['Category'],
                        'status': 'failed'
                    }
                
                # Be nice to the server
                time.sleep(2)
        
        return results


def main():
    """Main function to process CSV"""
    csv_path = "test2.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    print("🚀 PDF Manager Started")
    print("="*60)
    
    manager = PDFManager()
    results = manager.process_csv(csv_path)
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    failed_count = len(results) - success_count
    
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📁 PDFs saved to: {PDF_STORAGE.absolute()}")
    print(f"🖼️  Previews saved to: {PREVIEW_STORAGE.absolute()}")
    
    # Save results to JSON for later use
    import json
    with open('pdf_processing_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: pdf_processing_results.json")


if __name__ == "__main__":
    main()
