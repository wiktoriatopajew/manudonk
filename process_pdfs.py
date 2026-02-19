"""
Complete PDF Processing Pipeline
Downloads PDFs, generates previews, uploads to Google Drive
"""
import sys
import json
from pathlib import Path
from pdf_manager import PDFManager
from google_drive_manager import GoogleDriveManager


def run_complete_pipeline(csv_path: str = "test2.csv"):
    """
    Run complete PDF processing pipeline
    
    Steps:
    1. Download PDFs from URLs in CSV
    2. Generate preview images (first 5 pages)
    3. Upload PDFs to Google Drive
    4. Save all results with links
    
    Args:
        csv_path: Path to CSV file with product data
    """
    print("="*70)
    print("🚀 COMPLETE PDF PROCESSING PIPELINE")
    print("="*70)
    
    # Step 1: Download PDFs and generate previews
    print("\n📥 STEP 1: Downloading PDFs and generating previews...")
    print("-"*70)
    
    pdf_manager = PDFManager()
    download_results = pdf_manager.process_csv(csv_path)
    
    if not download_results:
        print("❌ No PDFs were downloaded. Exiting.")
        return
    
    # Step 2: Upload to Google Drive
    print("\n☁️  STEP 2: Uploading to Google Drive...")
    print("-"*70)
    
    drive_manager = GoogleDriveManager()
    
    if not drive_manager.service:
        print("\n⚠️  Google Drive not configured!")
        print("📝 Follow instructions in GOOGLE_DRIVE_SETUP.md")
        print("\nYou can still use locally stored PDFs without Google Drive.")
        
        # Ask user if they want to continue without upload
        response = input("\nContinue without Google Drive upload? (y/n): ")
        if response.lower() != 'y':
            print("Exiting. Run again after configuring Google Drive.")
            return
    else:
        # Upload all PDFs
        upload_results = {}
        
        for product_id, data in download_results.items():
            if data['status'] == 'success':
                pdf_path = Path(data['pdf_path'])
                
                if pdf_path.exists():
                    link = drive_manager.upload_pdf(
                        pdf_path,
                        int(product_id),
                        data['title']
                    )
                    
                    if link:
                        download_results[product_id]['google_drive_link'] = link
                        download_results[product_id]['delivery_method'] = 'google_drive'
                        upload_results[product_id] = {
                            'title': data['title'],
                            'google_drive_link': link,
                            'status': 'uploaded'
                        }
        
        # Save upload results
        with open('google_drive_upload_results.json', 'w', encoding='utf-8') as f:
            json.dump(upload_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Upload results saved to: google_drive_upload_results.json")
    
    # Step 3: Final results summary
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE!")
    print("="*70)
    
    success_count = sum(1 for r in download_results.values() if r['status'] == 'success')
    drive_count = sum(1 for r in download_results.values() if r.get('google_drive_link'))
    
    print(f"\n📊 Summary:")
    print(f"  • Downloaded: {success_count} PDFs")
    print(f"  • Uploaded to Drive: {drive_count} PDFs")
    print(f"  • Previews generated: {success_count} products")
    
    # Save final results
    with open('complete_results.json', 'w', encoding='utf-8') as f:
        json.dump(download_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Complete results: complete_results.json")
    
    # Next steps
    print("\n📋 Next Steps:")
    print("  1. Run: python update_database.py")
    print("     → Updates database with Google Drive links and preview images")
    print("  2. Check products on website")
    print("  3. Test purchasing a product")
    print("  4. Verify email delivery with Google Drive link")


def quick_test():
    """Quick test with first product only"""
    print("🧪 Quick Test Mode - Processing first product only\n")
    
    pdf_manager = PDFManager()
    
    # Read first product from CSV
    import csv
    with open('test2.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row = next(reader)
    
    product_id = int(row['ID'])
    title = row['English Title']
    pdf_url = row['Link PDF']
    
    print(f"Testing with: {title}")
    
    # Download
    pdf_path = pdf_manager.download_pdf(pdf_url, product_id, title)
    
    if pdf_path:
        # Generate preview
        previews = pdf_manager.generate_preview_images(pdf_path, product_id)
        print(f"\n✅ Test successful!")
        print(f"   PDF: {pdf_path}")
        print(f"   Previews: {len(previews)} images")
    else:
        print("❌ Test failed")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            quick_test()
        elif command == "full":
            csv_file = sys.argv[2] if len(sys.argv) > 2 else "test2.csv"
            run_complete_pipeline(csv_file)
        else:
            print("Usage:")
            print("  python process_pdfs.py test       # Quick test with first product")
            print("  python process_pdfs.py full       # Process all products")
            print("  python process_pdfs.py full file.csv  # Process custom CSV")
    else:
        # Interactive mode
        print("="*70)
        print("PDF PROCESSING SYSTEM")
        print("="*70)
        print("\nWhat would you like to do?")
        print("1. Quick test (first product only)")
        print("2. Process all products from test2.csv")
        print("3. Process custom CSV file")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ")
        
        if choice == "1":
            quick_test()
        elif choice == "2":
            run_complete_pipeline("test2.csv")
        elif choice == "3":
            csv_file = input("Enter CSV filename: ")
            run_complete_pipeline(csv_file)
        else:
            print("Goodbye!")


if __name__ == "__main__":
    main()
