# LLM Token Storage

## Overview

The application securely stores your Vertafore API key locally for convenient reuse.

## File Location

```
C:\Satish\AI\MRComments_Extractor\llm_token.json
```

## File Format

```json
{
  "token": "your-vertafore-api-key-here",
  "provider": "vertafore"
}
```

## How It Works

### 1. Saving Your API Key

- Enter your Vertafore API key in the GUI input field
- Click the **"Save API Key"** button
- The key is encrypted and saved to `llm_token.json`
- You'll see a success message confirming the save

### 2. Automatic Loading

- When you start the application, it automatically loads your saved API key
- You don't need to re-enter it each time
- The key appears masked (\*\*\*\*) in the input field

### 3. Clearing the API Key

- Click the **"Clear API Key"** button to remove both:
  - The key from the interface
  - The `llm_token.json` file from disk

## Security Features

### File Permissions

- On Unix/Linux systems, the file is set to `0600` (owner read/write only)
- On Windows, standard user-level permissions apply

### Version Control

- Token files are excluded from Git via `.gitignore`
- Your API key will never be committed to version control

### Best Practices

1. **Never share** your `llm_token.json` file
2. **Don't commit** token files to repositories
3. **Rotate keys** periodically per your security policy
4. **Delete** the token file when not in use for extended periods

## Troubleshooting

### Token Not Loading

1. Check if `llm_token.json` exists in the application directory
2. Verify the file is valid JSON format
3. Ensure file permissions allow reading

### Token Not Saving

1. Check write permissions in the application directory
2. Ensure sufficient disk space
3. Check application logs for error messages

## Related Files

- **Token Manager**: `utils/token_manager.py` - Handles all token operations
- **GitLab Token**: `token.json` - Stores GitLab Personal Access Token
- **Git Ignore**: `.gitignore` - Excludes sensitive files from version control

## API Integration

The saved token is used with:

- **Endpoint**: `https://api.dev.env.apps.vertafore.com/shirley/v1/PLATFORM-ADMIN-WEB-UI/VERTAFORE/entities/VERTAFORE/conversations`
- **Method**: POST
- **Authentication**: Bearer token in Authorization header
- **Model**: Claude Sonnet 3.5 via Vertafore's enterprise platform
