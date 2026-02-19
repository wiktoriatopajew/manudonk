"""
Google Drive OAuth 2.0 Setup
Run this once to authenticate with your personal Google account
"""
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def setup_oauth():
    """
    Setup OAuth 2.0 for Google Drive
    This will open a browser window for you to login with your Google account
    """
    creds = None
    
    # Check if we already have credentials
    if os.path.exists('token.pickle'):
        print("🔍 Found existing credentials...")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("🌐 Opening browser for Google authentication...")
            print("=" * 60)
            print("📝 Instructions:")
            print("1. Browser will open with Google login")
            print("2. Login with your personal Google account")
            print("3. Allow access to Google Drive")
            print("4. You may see a warning 'App isn't verified'")
            print("5. Click 'Advanced' → 'Go to app (unsafe)'")
            print("=" * 60)
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'google_oauth_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        
        print("✅ Authentication successful!")
        print("📁 Credentials saved to token.pickle")
    else:
        print("✅ Already authenticated!")
    
    return creds

if __name__ == "__main__":
    print("🔐 Google Drive OAuth 2.0 Setup")
    print("=" * 60)
    
    if not os.path.exists('google_oauth_credentials.json'):
        print("❌ Missing google_oauth_credentials.json!")
        print()
        print("📝 Follow these steps:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Select your project (or create one)")
        print("3. Enable Google Drive API")
        print("4. Go to 'Credentials'")
        print("5. Click 'Create Credentials' → 'OAuth 2.0 Client ID'")
        print("6. Application type: 'Desktop app'")
        print("7. Download the JSON file")
        print("8. Rename it to: google_oauth_credentials.json")
        print("9. Place it in this folder")
        print("10. Run this script again")
        print("=" * 60)
    else:
        try:
            setup_oauth()
            print()
            print("=" * 60)
            print("✅ Setup complete!")
            print("🚀 You can now upload PDFs to Google Drive")
            print("💡 Run: python test_upload.py")
            print("=" * 60)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
