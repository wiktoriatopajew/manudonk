"""
Extract OAuth refresh token from token.pickle
This can be used on Railway for automated authentication
"""
import pickle
import json

with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)
    
    print("OAuth Credentials extracted:")
    print("=" * 50)
    
    oauth_config = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    
    print(json.dumps(oauth_config, indent=2))
    print("=" * 50)
    print("\nCopy this entire JSON and add to Railway as:")
    print("GOOGLE_OAUTH_CREDENTIALS_JSON")
