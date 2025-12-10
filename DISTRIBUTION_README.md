# GitLab MR Comments Viewer

A desktop application for extracting and analyzing GitLab merge request comments with AI-powered best practices extraction.

## Features

- 🔍 Browse and search GitLab projects and merge requests
- 💬 Fetch and review merge request comments
- 🤖 AI-powered extraction of coding standards using Claude Sonnet 3.5
- 📊 Export standards to Excel (SharePoint/Teams compatible)
- 🔐 Secure token management

## Installation

1. Extract the zip file to your desired location
2. Run `GitLabMRViewer.exe`

## First-Time Setup

### 1. Configure Tokens

On first run, go to the **Settings** tab:

#### GitLab Personal Access Token

- Go to GitLab → Settings → Access Tokens
- Create a token with `api` scope
- Copy and save it in the Settings tab
- Click "Test Connection" to verify

#### Vertafore Enterprise AI Token

- Obtain your Vertafore API token from your administrator
- Save it in the Settings tab

Both tokens are stored locally in:

- `token.json` (GitLab)
- `llm_token.json` (Vertafore AI)

**Security Note**: These files contain sensitive tokens. Keep them secure and never share them.

## Usage

### Step 1: Load Projects

1. Click "Load Projects" to fetch your GitLab projects
2. Select a project from the dropdown

### Step 2: Browse Merge Requests

1. Choose MR state filter (merged/opened/closed/all)
2. Click "Load MRs"
3. Select an MR from the dropdown (or paste MR URL directly)

### Step 3: Fetch Comments

1. Click "🔄 Fetch Comments"
2. Review comments in the "Comments Review" tab

### Step 4: Extract Best Practices

1. Check/uncheck discussions you want to analyze
2. Click "🤖 Extract Best Practices"
3. View extracted coding standards in "Best Practices" tab

### Step 5: Export Standards

1. Select standards type (UI Standards or Java Standards)
2. Click "📋 Copy Standards" to copy to clipboard
3. Or click "📊 Export to Excel" to save as file
4. Paste into your SharePoint/Teams Excel checklist

## Token File Format

If you prefer to create token files manually:

**token.json:**

```json
{
  "token": "your-gitlab-personal-access-token"
}
```

**llm_token.json:**

```json
"your-vertafore-api-token"
```

## Troubleshooting

### "No tokens found" error

- Go to Settings tab and configure your tokens
- Or manually create `token.json` and `llm_token.json` files next to the executable

### "Failed to fetch comments"

- Verify your GitLab token is valid (use "Test Connection")
- Check that you have access to the merge request
- Ensure the MR URL is correct

### "Failed to extract best practices"

- Verify your Vertafore AI token is configured
- Check your internet connection
- Ensure you have selected at least one discussion

## System Requirements

- Windows 10/11
- Internet connection (for GitLab and AI API access)
- 4GB RAM minimum

## Privacy & Security

- All tokens are stored locally on your machine
- Tokens are never sent to external services except GitLab and Vertafore APIs
- No telemetry or usage tracking
- Your data never leaves your control

## Support

For issues or questions, contact your team administrator.

## Version

Version 1.0.0
Built with Python, tkinter, and Claude Sonnet 3.5
