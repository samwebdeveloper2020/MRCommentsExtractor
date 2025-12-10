# Quick Start: Getting Microsoft Graph Token

## Option 1: Using the Automated Script (Easiest)

### Step 1: Get Azure AD Credentials

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Find or create your app registration (e.g., "MR Comments Extractor")
4. Copy these values:
   - **Tenant ID** (from Overview page)
   - **Client ID** / Application ID (from Overview page)
   - **Client Secret** (from Certificates & secrets)

If you don't have a client secret:

- Go to **Certificates & secrets** → **New client secret**
- Add description and expiration
- **Copy the secret value immediately** (it won't be shown again!)

### Step 2: Run the Token Generator

**Double-click `generate_token.bat`**

Or run manually:

```bash
python generate_graph_token.py
```

### Step 3: Enter Your Credentials

When prompted, enter:

- Tenant ID
- Client ID
- Client Secret

The script will:

- Save your config to `graph_token.json`
- Generate an access token
- Save the token to the same file

**Done!** You can now use the Export to Excel feature.

---

## Option 2: Manual Token Generation

### Using PowerShell

```powershell
# Install msal if needed
pip install msal

# Run the generator
python generate_graph_token.py
```

### Using Python directly

```python
import msal
import json

# Your Azure AD app credentials
config = {
    "tenant_id": "your-tenant-id-here",
    "client_id": "your-client-id-here",
    "client_secret": "your-client-secret-here"
}

# Create MSAL app
app = msal.ConfidentialClientApplication(
    config['client_id'],
    authority=f"https://login.microsoftonline.com/{config['tenant_id']}",
    client_credential=config['client_secret']
)

# Get token
result = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"]
)

if "access_token" in result:
    config['token'] = result['access_token']
    with open('graph_token.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("Token saved!")
else:
    print(f"Error: {result.get('error_description')}")
```

---

## Troubleshooting

### "MSAL not installed"

```bash
conda run -p .conda pip install msal
```

### "Invalid client secret"

- Client secrets expire! Create a new one in Azure Portal
- Make sure you copied the **Value**, not the **Secret ID**

### "Admin consent required"

Your IT admin needs to grant permissions:

1. Azure Portal → App registrations → Your app
2. API permissions → Grant admin consent
3. Required permissions:
   - `Files.ReadWrite.All`
   - `Sites.ReadWrite.All`

### "Token expired"

Tokens last ~1 hour. Just run `generate_token.bat` again to get a fresh token.

---

## Token File Location

The token is saved in: `graph_token.json`

**Never commit this file to git!** (It's already in .gitignore)

---

## What Next?

Once you have a valid token in `graph_token.json`:

1. Extract coding standards from MR comments
2. Go to "Best Practices" tab
3. Paste your Teams/SharePoint Excel URL
4. Click "Export to Excel"
5. Done! The standards are written directly to the file.

---

## Need Help?

- **Azure AD Setup**: See `GRAPH_API_SETUP.md` for detailed instructions
- **API Permissions**: Contact your IT admin
- **Token Issues**: Re-run `generate_token.bat`
