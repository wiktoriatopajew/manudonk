"""
Google Drive Manager for Railway - Using OAuth
Uses OAuth refresh token for automated authentication without browser
"""
import os
import json
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class GoogleDriveManagerRailway:
    """Google Drive manager using OAuth refresh token (for Railway)"""
    
    def __init__(self):
        """Initialize with OAuth from environment or Service Account as fallback"""
        self.service = None
        self.folder_id = None
        
        # Try OAuth first (preferred - has storage quota)
        oauth_json = os.getenv('GOOGLE_OAUTH_CREDENTIALS_JSON')
        
        if oauth_json:
            try:
                oauth_dict = json.loads(oauth_json)
                credentials = Credentials(
                    token=oauth_dict.get('token'),
                    refresh_token=oauth_dict.get('refresh_token'),
                    token_uri=oauth_dict.get('token_uri'),
                    client_id=oauth_dict.get('client_id'),
                    client_secret=oauth_dict.get('client_secret'),
                    scopes=oauth_dict.get('scopes', ['https://www.googleapis.com/auth/drive'])
                )
                self.service = build('drive', 'v3', credentials=credentials)
                print("✅ Google Drive authenticated (OAuth from environment)")
            except Exception as e:
                print(f"❌ Error with OAuth credentials: {str(e)}")
        
        # Fallback to Service Account (old method)
        if not self.service:
            creds_json = os.getenv('GOOGLE_DRIVE_CREDENTIALS_JSON')
            if creds_json:
                try:
                    creds_dict = json.loads(creds_json)
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_dict,
                        scopes=['https://www.googleapis.com/auth/drive']
                    )
                    self.service = build('drive', 'v3', credentials=credentials)
                    print("✅ Google Drive authenticated (Service Account from environment)")
                except Exception as e:
                    print(f"❌ Error with Service Account credentials: {str(e)}")
        
        # Fallback to local file (development)
        elif os.path.exists('google_drive_credentials.json'):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    'google_drive_credentials.json',
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                self.service = build('drive', 'v3', credentials=credentials)
                print("✅ Google Drive authenticated (from file)")
            except Exception as e:
                print(f"❌ Error with file credentials: {str(e)}")
        
        else:
            print("⚠️  No Google Drive credentials found!")
            print("Set GOOGLE_DRIVE_CREDENTIALS_JSON env var or add google_drive_credentials.json")
        
        # Load folder ID from environment or config
        self.folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        print(f"🔍 DEBUG: GOOGLE_DRIVE_FOLDER_ID from env: {self.folder_id}")
        if not self.folder_id:
            self._load_folder_config()
        else:
            print(f"✅ Using folder ID: {self.folder_id}")
    
    def _load_folder_config(self):
        """Load folder ID from config file"""
        try:
            if os.path.exists('google_drive_config.json'):
                with open('google_drive_config.json', 'r') as f:
                    config = json.load(f)
                    self.folder_id = config.get('folder_id')
        except Exception as e:
            print(f"⚠️  Could not load folder config: {str(e)}")
    
    def create_folder(self, folder_name: str = "Manuals Store PDFs") -> Optional[str]:
        """
        Create folder in Google Drive
        
        Args:
            folder_name: Folder name
        
        Returns:
            Folder ID or None
        """
        if not self.service:
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
            
            print(f"✅ Created folder: {folder_name} (ID: {folder_id})")
            print(f"📝 Add to Railway env: GOOGLE_DRIVE_FOLDER_ID={folder_id}")
            
            # Save to config file (for development)
            with open('google_drive_config.json', 'w') as f:
                json.dump({'folder_id': folder_id}, f)
            
            return folder_id
            
        except HttpError as e:
            print(f"❌ Error creating folder: {str(e)}")
            return None
    
    def upload_pdf(self, file_path: Path, product_id: int, title: str) -> Optional[str]:
        """
        Upload PDF to Google Drive and return shareable link
        
        Args:
            file_path: Path to PDF file (can be temp file)
            product_id: Product ID
            title: Product title
        
        Returns:
            Download link or None
        """
        if not self.service:
            print("❌ Google Drive not authenticated")
            return None
        
        # Create folder if needed
        if not self.folder_id:
            self.create_folder()
            if not self.folder_id:
                print("❌ Could not create/find Google Drive folder")
                return None
        
        try:
            # Clean title for filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title[:100]
            
            file_metadata = {
                'name': f"{product_id}_{safe_title}.pdf",
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(
                str(file_path),
                mimetype='application/pdf',
                resumable=True
            )
            
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            file_id = file.get('id')
            
            # Make publicly accessible (anyone with link can view)
            self.service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            # Return direct download link
            download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            print(f"✅ Uploaded to Google Drive")
            print(f"   Link: {download_link}")
            
            return download_link
            
        except HttpError as e:
            print(f"❌ Upload error: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return None


def test_authentication():
    """Test Google Drive authentication"""
    print("="*70)
    print("🧪 Testing Google Drive Authentication")
    print("="*70)
    
    manager = GoogleDriveManagerRailway()
    
    if manager.service:
        print("\n✅ Authentication successful!")
        
        if manager.folder_id:
            print(f"✅ Folder ID: {manager.folder_id}")
        else:
            print("⚠️  No folder ID configured")
            response = input("Create new folder? (y/n): ")
            if response.lower() == 'y':
                manager.create_folder()
    else:
        print("\n❌ Authentication failed!")
        print("\nSetup instructions:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create project and enable Google Drive API")
        print("3. Create Service Account")
        print("4. Download JSON key")
        print("5. Save as 'google_drive_credentials.json' or set GOOGLE_DRIVE_CREDENTIALS_JSON env var")


if __name__ == "__main__":
    test_authentication()
