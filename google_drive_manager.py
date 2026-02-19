"""
Google Drive Upload Manager
"""
import os
import json
import pickle
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class GoogleDriveManager:
    """Manage Google Drive uploads and sharing"""
    
    def __init__(self, token_path: str = "token.pickle"):
        """
        Initialize Google Drive manager
        
        Args:
            token_path: Path to OAuth 2.0 token pickle file
        """
        self.token_path = token_path
        self.service = None
        self.folder_id = None
        
        if os.path.exists(token_path):
            self._authenticate()
        else:
            print("⚠️  Google Drive not authenticated!")
            print("📝 Run: python setup_google_oauth.py")
    
    def _authenticate(self):
        """Authenticate with Google Drive API using OAuth 2.0"""
        try:
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
            
            # Refresh token if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('drive', 'v3', credentials=creds)
            print("✅ Google Drive authenticated successfully")
            
        except Exception as e:
            print(f"❌ Error authenticating with Google Drive: {str(e)}")
    
    def create_folder(self, folder_name: str = "Manuals Store PDFs") -> Optional[str]:
        """
        Create a folder in Google Drive
        
        Args:
            folder_name: Name of the folder
        
        Returns:
            Folder ID or None if failed
        """
        if not self.service:
            print("❌ Google Drive not authenticated")
            return None
        
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            self.folder_id = folder_id
            
            print(f"✅ Folder created: {folder_name} (ID: {folder_id})")
            
            # Save folder ID for future use
            with open('google_drive_config.json', 'w') as f:
                json.dump({'folder_id': folder_id}, f)
            
            return folder_id
            
        except HttpError as e:
            print(f"❌ Error creating folder: {str(e)}")
            return None
    
    def load_folder_id(self) -> Optional[str]:
        """Load existing folder ID from config"""
        try:
            if os.path.exists('google_drive_config.json'):
                with open('google_drive_config.json', 'r') as f:
                    config = json.load(f)
                    self.folder_id = config.get('folder_id')
                    return self.folder_id
        except Exception as e:
            print(f"⚠️  Could not load folder ID: {str(e)}")
        return None
    
    def upload_pdf(self, file_path: Path, product_id: int, title: str, check_existing: bool = True) -> Optional[str]:
        """
        Upload PDF to Google Drive (only if not already uploaded)
        
        Args:
            file_path: Path to PDF file
            product_id: Product ID
            title: Product title
            check_existing: Check if product already has Google Drive link in database
        
        Returns:
            Shareable link or None if failed
        """
        if not self.service:
            print("❌ Google Drive not authenticated")
            return None
        
        # Check if product already has a Google Drive link
        if check_existing:
            from database.models import Product, get_session
            session = get_session()
            try:
                product = session.query(Product).filter(Product.id == product_id).first()
                if product and product.google_drive_link:
                    print(f"✅ Product {product_id} already has Google Drive link")
                    print(f"   Reusing existing link: {product.google_drive_link[:50]}...")
                    return product.google_drive_link
            finally:
                session.close()
        
        # Load or create folder
        if not self.folder_id:
            self.load_folder_id()
            if not self.folder_id:
                self.create_folder()
        
        try:
            print(f"📤 Uploading to Google Drive: {title}...")
            
            file_metadata = {
                'name': f"{product_id}_{title}.pdf",
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            media = MediaFileUpload(
                str(file_path),
                mimetype='application/pdf',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, webContentLink'
            ).execute()
            
            file_id = file.get('id')
            
            # Make file accessible to anyone with the link
            self.service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            # Get shareable link
            download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            view_link = file.get('webViewLink')
            
            print(f"✅ Uploaded successfully!")
            print(f"   View: {view_link}")
            print(f"   Download: {download_link}")
            
            return download_link
            
        except HttpError as e:
            print(f"❌ Error uploading file: {str(e)}")
            return None
    
    def upload_all_from_results(self, results_path: str = "pdf_processing_results.json"):
        """
        Upload all PDFs from processing results
        
        Args:
            results_path: Path to results JSON file
        """
        if not os.path.exists(results_path):
            print(f"❌ Results file not found: {results_path}")
            return
        
        with open(results_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        upload_results = {}
        
        for product_id, data in results.items():
            if data['status'] == 'success':
                pdf_path = Path(data['pdf_path'])
                
                if pdf_path.exists():
                    link = self.upload_pdf(pdf_path, int(product_id), data['title'])
                    
                    if link:
                        upload_results[product_id] = {
                            'title': data['title'],
                            'google_drive_link': link,
                            'status': 'uploaded'
                        }
                    else:
                        upload_results[product_id] = {
                            'title': data['title'],
                            'status': 'upload_failed'
                        }
        
        # Save upload results
        with open('google_drive_upload_results.json', 'w', encoding='utf-8') as f:
            json.dump(upload_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Upload results saved to: google_drive_upload_results.json")


def main():
    """Test Google Drive functionality"""
    print("🚀 Google Drive Manager")
    print("="*60)
    
    manager = GoogleDriveManager()
    
    if manager.service:
        print("\n📤 Ready to upload PDFs to Google Drive")
        print("💡 Run: manager.upload_all_from_results()")
    else:
        print("\n⚠️  Setup required! Follow these steps:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable Google Drive API")
        print("4. Create Service Account credentials")
        print("5. Download JSON and save as 'google_drive_credentials.json'")


if __name__ == "__main__":
    main()
