"""
Railway PDF Processor - For Railway deployment
Downloads PDFs from urls and uploads directly to Google Drive
No local storage (Railway filesystem is ephemeral)
"""
import os
import requests
import tempfile
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product
from google_drive_manager_railway import GoogleDriveManagerRailway


class RailwayPDFProcessor:
    """Process PDFs on Railway - download from URL and upload to Google Drive"""
    
    def __init__(self):
        # Database connection
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not set")
        
        # Fix postgres:// to postgresql:// for SQLAlchemy
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Google Drive manager
        self.drive = GoogleDriveManagerRailway()
        
        # HTTP session for downloads
        self.http_session = requests.Session()
        self.http_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_pdf_to_memory(self, url: str, product_id: int, title: str) -> Optional[bytes]:
        """
        Download PDF directly to memory (no local storage)
        
        Args:
            url: PDF download URL
            product_id: Product ID
            title: Product title
        
        Returns:
            PDF content as bytes or None if failed
        """
        try:
            print(f"📥 Downloading PDF for: {title}...")
            
            response = self.http_session.get(url, timeout=120)
            response.raise_for_status()
            
            # Verify it's a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                print(f"⚠️  Warning: Content-Type is {content_type}, expected PDF")
            
            size_mb = len(response.content) / (1024 * 1024)
            print(f"✅ Downloaded: {size_mb:.2f} MB")
            
            return response.content
            
        except Exception as e:
            print(f"❌ Error downloading PDF: {str(e)}")
            return None
    
    def process_product(self, product_id: int) -> bool:
        """
        Process single product:
        1. Get product from database
        2. Download PDF from pdf_url
        3. Upload to Google Drive
        4. Update google_drive_link in database
        
        Args:
            product_id: Product ID to process
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get product from database
            product = self.session.query(Product).filter_by(id=product_id).first()
            
            if not product:
                print(f"❌ Product {product_id} not found in database")
                return False
            
            if not product.pdf_url:
                print(f"❌ Product {product_id} has no pdf_url")
                return False
            
            # Check if already processed
            if product.google_drive_link:
                print(f"✅ Product {product_id} already has Google Drive link")
                return True
            
            print(f"\n🔄 Processing: {product.title} (ID: {product_id})")
            
            # Download PDF to memory
            pdf_content = self.download_pdf_to_memory(
                product.pdf_url,
                product_id,
                product.title
            )
            
            if not pdf_content:
                return False
            
            # Create temporary file for upload
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_path = Path(temp_file.name)
            
            try:
                # Upload to Google Drive
                print(f"☁️  Uploading to Google Drive...")
                drive_link = self.drive.upload_pdf(
                    temp_path,
                    product_id,
                    product.title
                )
                
                if drive_link:
                    # Update database
                    product.google_drive_link = drive_link
                    product.pdf_processed = True
                    self.session.commit()
                    
                    print(f"✅ Success! Google Drive link: {drive_link}")
                    return True
                else:
                    print(f"❌ Failed to upload to Google Drive")
                    return False
                    
            finally:
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()
            
        except Exception as e:
            print(f"❌ Error processing product {product_id}: {str(e)}")
            self.session.rollback()
            return False
    
    def process_all_pending(self, limit: Optional[int] = None):
        """
        Process all products that have pdf_url but no google_drive_link
        
        Args:
            limit: Maximum number of products to process (None = all)
        """
        print("="*70)
        print("🚀 RAILWAY PDF PROCESSOR")
        print("="*70)
        
        # Find products needing processing
        query = self.session.query(Product).filter(
            Product.pdf_url.isnot(None),
            Product.google_drive_link.is_(None)
        )
        
        if limit:
            query = query.limit(limit)
        
        products = query.all()
        
        if not products:
            print("\n✅ No products need processing!")
            return
        
        print(f"\n📊 Found {len(products)} products to process")
        
        success_count = 0
        failed_count = 0
        
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}]", end=' ')
            
            if self.process_product(product.id):
                success_count += 1
            else:
                failed_count += 1
        
        # Summary
        print("\n" + "="*70)
        print("✅ PROCESSING COMPLETE")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"  • Successful: {success_count}")
        print(f"  • Failed: {failed_count}")
        print(f"  • Total: {len(products)}")
    
    def close(self):
        """Close database connection"""
        self.session.close()


def main():
    """Main entry point"""
    import sys
    
    processor = RailwayPDFProcessor()
    
    try:
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "test":
                # Process first pending product only
                print("🧪 Test mode - processing first product\n")
                processor.process_all_pending(limit=1)
            
            elif command == "all":
                # Process all pending products
                processor.process_all_pending()
            
            elif command.isdigit():
                # Process specific product ID
                product_id = int(command)
                processor.process_product(product_id)
            
            else:
                print("Usage:")
                print("  python railway_pdf_processor.py test      # Process first product")
                print("  python railway_pdf_processor.py all       # Process all pending")
                print("  python railway_pdf_processor.py 185871    # Process specific ID")
        else:
            # Default: process all
            processor.process_all_pending()
    
    finally:
        processor.close()


if __name__ == "__main__":
    main()
