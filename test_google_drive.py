"""
Test Google Drive Connection
"""
from google_drive_manager import GoogleDriveManager

def test_connection():
    print("🧪 Testing Google Drive Connection...")
    print("="*60)
    
    try:
        drive = GoogleDriveManager()
        
        if drive.service:
            print("✅ Successfully connected to Google Drive!")
            print(f"📁 Using folder: Manuals Store")
            
            # Try to list files in root
            results = drive.service.files().list(
                pageSize=5,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            print(f"\n✅ Can access Drive! Found {len(files)} items")
            
            if files:
                print("\n📄 Sample files/folders:")
                for f in files[:5]:
                    print(f"  • {f['name']}")
            
            return True
        else:
            print("❌ Failed to initialize Google Drive service")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    
    if success:
        print("\n" + "="*60)
        print("✅ Google Drive is ready to use!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ Google Drive setup incomplete")
        print("📝 Check GOOGLE_DRIVE_SETUP.md for instructions")
        print("="*60)
