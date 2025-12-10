"""
Script to generate Microsoft Graph API token for SharePoint/Teams access
Run this script to get an access token for exporting to Excel files
"""

import json
from pathlib import Path

def generate_graph_token():
    """Generate Microsoft Graph API token using MSAL"""
    
    print("=" * 70)
    print("Microsoft Graph API Token Generator")
    print("=" * 70)
    print()
    
    # Check if config exists
    config_file = Path("graph_token.json")
    
    if not config_file.exists():
        print("graph_token.json not found. Let's create it.")
        print()
        print("You'll need the following from Azure Portal:")
        print("1. Tenant ID (Directory ID)")
        print("2. Client ID (Application ID)")
        print("3. Client Secret")
        print()
        print("See GRAPH_API_SETUP.md for detailed setup instructions.")
        print()
        
        tenant_id = input("Enter your Tenant ID: ").strip()
        client_id = input("Enter your Client ID (Application ID): ").strip()
        client_secret = input("Enter your Client Secret: ").strip()
        
        config = {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "token": ""
        }
        
        with open("graph_token.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\nConfiguration saved to graph_token.json")
    else:
        print("Loading configuration from graph_token.json...")
        with open(config_file, 'r') as f:
            config = json.load(f)
    
    # Try to import msal
    try:
        import msal
    except ImportError:
        print("\nERROR: msal library not installed.")
        print("Please install it using:")
        print("  conda run -p .conda pip install msal")
        print("  or")
        print("  pip install msal")
        return False
    
    print("\nGenerating access token...")
    print(f"Tenant: {config['tenant_id']}")
    print(f"Client: {config['client_id']}")
    
    # Create MSAL confidential client application
    try:
        authority = f"https://login.microsoftonline.com/{config['tenant_id']}"
        app = msal.ConfidentialClientApplication(
            config['client_id'],
            authority=authority,
            client_credential=config['client_secret']
        )
        
        # Acquire token for Microsoft Graph
        scopes = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            # Save the token
            config['token'] = result['access_token']
            
            with open("graph_token.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            print("\n" + "=" * 70)
            print("SUCCESS! Access token generated and saved.")
            print("=" * 70)
            print(f"\nToken expires in: {result.get('expires_in', 'unknown')} seconds (~1 hour)")
            print("\nYou can now export coding standards to SharePoint/Teams Excel files!")
            print("\nNote: The token will expire in about 1 hour. Run this script again")
            print("      when you need to refresh the token.")
            
            return True
        else:
            print("\n" + "=" * 70)
            print("ERROR: Failed to acquire token")
            print("=" * 70)
            print(f"\nError: {result.get('error')}")
            print(f"Description: {result.get('error_description')}")
            print(f"Correlation ID: {result.get('correlation_id')}")
            print("\nCommon issues:")
            print("1. Invalid client secret (may have expired)")
            print("2. Incorrect tenant ID or client ID")
            print("3. App not granted admin consent for permissions")
            print("4. Required API permissions not configured")
            print("\nPlease check your Azure AD app configuration.")
            
            return False
            
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR: Exception occurred")
        print("=" * 70)
        print(f"\n{str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    generate_graph_token()
    input("\nPress Enter to exit...")
