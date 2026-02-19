"""
Quick Upload Test - Upload one PDF to Google Drive
"""
from google_drive_manager import GoogleDriveManager
from pathlib import Path

def test_upload():
    print("🧪 Testing PDF Upload to Google Drive...")
    print("="*60)
    
    # Find first downloaded PDF
    pdf_folder = Path("storage/pdfs")
    pdf_files = list(pdf_folder.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDFs found in storage/pdfs/")
        print("💡 Run: python process_pdfs.py test")
        return False
    
    pdf_file = pdf_files[0]
    print(f"📄 Found PDF: {pdf_file.name}")
    print(f"   Size: {pdf_file.stat().st_size / (1024*1024):.2f} MB")
    
    # Upload to Google Drive
    print(f"\n☁️  Uploading to Google Drive...")
    
    drive = GoogleDriveManager()
    
    if not drive.service:
        print("❌ Google Drive not configured")
        return False
    
    try:
        # Upload with check_existing=False to force new upload for testing
        link = drive.upload_pdf(
            file_path=pdf_file,
            product_id=999999,  # Test ID
            title="Test Upload",
            check_existing=False  # Force upload for testing
        )
        
        if link:
            print(f"✅ Upload successful!")
            print(f"📎 Google Drive Link: {link}")
            
            # Test if link is accessible
            print(f"\n🔗 Link to test in browser:")
            print(f"   {link}")
            
            return True
        else:
            print(f"❌ Upload failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_upload()
    
    if success:
        print("\n" + "="*60)
        print("✅ Upload test successful!")
        print("🚀 Ready to process all products")
        print("💡 Run: python process_pdfs.py full")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ Upload test failed")
        print("="*60)
