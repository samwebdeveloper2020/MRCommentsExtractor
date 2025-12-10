# Microsoft Graph API Setup for SharePoint/Teams Excel Export

This guide explains how to set up Microsoft Graph API access to enable direct export of coding standards to SharePoint/Teams Excel files.

## Prerequisites

- Azure AD admin access (or approval from IT)
- Microsoft 365 subscription with SharePoint/Teams
- Python packages: `msal`, `requests`

## Setup Steps

### 1. Register Application in Azure AD

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Configure:
   - **Name**: `MR Comments Extractor`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: Leave blank for now
5. Click **Register**

### 2. Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph** → **Delegated permissions**
4. Add these permissions:
   - `Files.ReadWrite.All` - Read and write all files
   - `Sites.ReadWrite.All` - Read and write items in all site collections
5. Click **Add permissions**
6. Click **Grant admin consent** (requires admin)

### 3. Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add description: `MR Extractor Secret`
4. Set expiration (recommended: 24 months)
5. Click **Add**
6. **IMPORTANT**: Copy the secret value immediately (it won't be shown again)

### 4. Get Your Tenant ID

1. In Azure AD overview page, copy your **Tenant ID**
2. Also copy the **Application (client) ID** from your app registration

### 5. Configure graph_token.json

Create a file named `graph_token.json` in the project root:

```json
{
  "tenant_id": "your-tenant-id-here",
  "client_id": "your-application-client-id-here",
  "client_secret": "your-client-secret-here",
  "token": ""
}
```

Replace the values with your actual credentials from steps above.

### 6. Generate Access Token

The application will automatically generate an access token using MSAL when needed.

Alternatively, you can manually get a token:

```python
import msal
import json

# Load credentials
with open('graph_token.json', 'r') as f:
    config = json.load(f)

# Create MSAL app
app = msal.ConfidentialClientApplication(
    config['client_id'],
    authority=f"https://login.microsoftonline.com/{config['tenant_id']}",
    client_credential=config['client_secret']
)

# Get token
result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

if "access_token" in result:
    config['token'] = result['access_token']
    with open('graph_token.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("Token saved successfully!")
else:
    print(f"Error: {result.get('error_description')}")
```

## Usage

Once configured, you can export coding standards directly to SharePoint/Teams:

1. Extract best practices from review comments
2. In the "Best Practices" tab, paste your SharePoint/Teams Excel file URL:
   - SharePoint: `https://company.sharepoint.com/sites/sitename/Shared%20Documents/file.xlsx`
   - Teams: Copy link from Teams channel Files tab
3. Click **Export to Excel**
4. The coding standards will be written directly to the Excel file

## Supported URL Formats

- **SharePoint Direct**: `https://tenant.sharepoint.com/sites/sitename/Documents/file.xlsx`
- **Teams Channel**: Links from Teams Files tab
- **OneDrive for Business**: Shared OneDrive links

## Troubleshooting

### "No Graph API token found"

- Make sure `graph_token.json` exists with valid credentials
- Run the token generation script above

### "Could not parse SharePoint URL"

- Verify the URL format is correct
- Try using the direct file URL instead of a sharing link

### "Permission denied"

- Ensure admin has granted consent for the app
- Check that the app has `Files.ReadWrite.All` permission

### "Token expired"

- Tokens expire after ~1 hour
- Re-run the token generation script
- Consider implementing automatic token refresh

## Security Notes

- **Never commit `graph_token.json` to version control**
- The file is already in `.gitignore`
- Store credentials securely
- Rotate client secrets periodically
- Use least privilege - only grant necessary permissions

## Alternative: Manual Export

If Graph API setup is not possible, you can still:

1. Export to a local Excel file
2. Manually upload to SharePoint/Teams
3. The app will save the link reference in the file

## Support

For issues with Azure AD setup, contact your IT department or Microsoft support.
