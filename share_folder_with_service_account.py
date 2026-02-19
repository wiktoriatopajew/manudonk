"""
Share existing Google Drive folder with Service Account
Run this ONCE to grant proper permissions
"""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Folder ID
FOLDER_ID = "1fuchPndGleKsfyVYZSUvzsqwLSpVFqEG"

# Service Account email
SERVICE_ACCOUNT_EMAIL = "uploaderbot@gen-lang-client-0013085534.iam.gserviceaccount.com"

def share_folder():
    """Share folder with service account using OAuth credentials"""
    
    # Use token.pickle for OAuth authentication
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    import pickle
    
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("❌ No valid OAuth credentials found!")
            print("Run process_pdfs.py first to authenticate")
            return
    
    # Build Drive service
    service = build('drive', 'v3', credentials=creds)
    
    try:
        # Grant writer permission to service account
        permission = {
            'type': 'user',
            'role': 'writer',  # Full write access
            'emailAddress': SERVICE_ACCOUNT_EMAIL
        }
        
        result = service.permissions().create(
            fileId=FOLDER_ID,
            body=permission,
            sendNotificationEmail=False,
            fields='id'
        ).execute()
        
        print(f"✅ Successfully shared folder with Service Account!")
        print(f"   Folder ID: {FOLDER_ID}")
        print(f"   Service Account: {SERVICE_ACCOUNT_EMAIL}")
        print(f"   Permission ID: {result.get('id')}")
        print(f"\n🎉 Now Service Account can upload to this folder!")
        
    except Exception as e:
        print(f"❌ Error sharing folder: {str(e)}")

if __name__ == "__main__":
    share_folder()
