# GitLab MR Comments Viewer

A Python desktop application to extract and view merge request comments from GitLab.

## Features

- **Easy-to-use GUI**: Clean interface built with tkinter
- **Token Management**: Secure token input with validation
- **Comment Extraction**: Fetches all comments from GitLab merge requests with pagination support
- **Image Download & Display**: Automatically downloads and displays images from comments
- **Organized Display**:
  - All Comments tab: Shows all discussions and comments with image information
  - Code Comments tab: Shows only code-related comments with file/line information
  - Summary tab: Provides statistics, author breakdown, and image count
- **Image Viewer**: Dedicated window to view all downloaded images with thumbnails
- **Export Functionality**: Save comments as JSON files
- **Error Handling**: Comprehensive error handling for API calls and network issues## Requirements

- Python 3.11+
- requests library
- urllib3 library
- Pillow library (for image processing)
- tkinter (usually included with Python)

## Setup

1. The application is already set up in a conda environment
2. Required packages (requests, urllib3) are installed
3. All necessary files are created in the project directory

## How to Run

### Option 1: Using the batch file (Easiest)

Double-click `run_app.bat` to start the application

### Option 2: Using command line

```bash
C:/ProgramData/anaconda3/Scripts/conda.exe run -p c:\Satish\AI\MRComments_Extractor\.conda python main.py
```

## How to Use

1. **Setup Tokens (One-Time)**:

   **GitLab Personal Access Token:**

   - Go to GitLab → Settings → Access Tokens
   - Create a token with `api` scope
   - Copy the token
   - Create a file named `token.json` in the project root directory
   - Add your token in this format:
     ```json
     {
       "token": "your-gitlab-token-here",
       "gitlab_url": "https://gitlab.com"
     }
     ```

   **Vertafore API Key (for LLM Best Practices extraction):**

   - Obtain your Vertafore API key
   - Create a file named `llm_token.json` in the project root directory
   - Add your token in this format:
     ```json
     {
       "token": "your-vertafore-api-key-here"
     }
     ```

   **Important:** Both `token.json` and `llm_token.json` are automatically excluded from git via `.gitignore`

2. **Load Projects**:

   - Click "Load Projects" to fetch your GitLab projects (filters to certificate-forms projects)
   - Select a project from the dropdown

3. **Load Merge Requests**:

   - Choose MR state filter (opened, closed, merged, or all)
   - Click "Load MRs" to fetch merge requests for the selected project
   - Select an MR from the dropdown (MRs are sorted with latest first)

4. **Extract Comments**:

   - Click "Fetch Comments" to retrieve all discussions from the selected MR
   - Images from comments are automatically downloaded to the `images/` directory

5. **View Results**:

   - **All Comments Tab**: See all discussions and comments with image information
   - **Code Comments Tab**: See only code-related comments with file locations
   - **Summary Tab**: View statistics, author breakdown, and downloaded images
   - **Comments Review Tab**: Check/uncheck comments to include in best practices extraction
   - **Best Practices Tab**: View AI-extracted coding standards from selected comments

6. **Extract Best Practices** (requires Vertafore API key):

   - Go to the "Comments Review" tab
   - Check the comments you want to analyze
   - Click "Extract Best Practices" button
   - View the AI-generated coding standards in the "Best Practices" tab
   - See the prompt used for extraction at the bottom

7. **View Images**:

   - Click "View Images" to open image viewer window
   - Browse all downloaded images with thumbnails
   - Images are automatically downloaded to the `images/` directory

8. **Export Data**:
   - Click "Export to JSON" to save comments to a file

## Project Structure

```
MRComments_Extractor/
├── main.py                 # Application entry point
├── run_app.bat            # Easy launcher batch file
├── requirements.txt       # Python dependencies
├── token.json             # GitLab access token (create this file)
├── llm_token.json         # Vertafore API key (create this file)
├── .gitignore             # Excludes token files from git
├── images/                # Downloaded images from comments
├── prompts/
│   └── extract_best_practices.txt  # LLM prompt template
├── gui/
│   ├── __init__.py       # Package marker
│   └── main_window.py    # Main GUI implementation
├── services/
│   ├── __init__.py       # Package marker
│   ├── gitlab_api.py     # GitLab API integration
│   └── llm_service.py    # LLM service for best practices extraction
└── utils/
    ├── __init__.py       # Package marker
    ├── helpers.py        # Utility functions
    ├── token_manager.py  # Token storage and retrieval
    └── image_viewer.py   # Image display utilities
```

## Token Management

The application uses file-based token storage for security:

- **GitLab Token**: Stored in `token.json` in the project root
- **Vertafore API Key**: Stored in `llm_token.json` in the project root
- **Auto-Load**: Both tokens are automatically loaded when you start the app
- **Security**: Token files are excluded from git via `.gitignore`
- **Status Display**: The app shows which tokens are loaded on startup

## Troubleshooting

- **Token Issues**:
  - Ensure `token.json` exists with your GitLab token
  - Ensure `llm_token.json` exists with your Vertafore API key (if using best practices feature)
  - Make sure your GitLab token has `api` scope and is not expired
- **URL Format**: Ensure the MR URL follows the format: `https://gitlab.com/project/path/-/merge_requests/123`
- **Network Issues**: Check your internet connection and GitLab accessibility
- **Permission Issues**: Ensure you have access to view the merge request
- **Best Practices Not Working**: Verify your Vertafore API key is correct in `llm_token.json`

## Features Demonstrated

- ✅ GitLab API integration with pagination
- ✅ Personal Access Token authentication (file-based)
- ✅ Project filtering (certificate-forms projects)
- ✅ MR loading and filtering (opened/closed/merged/all)
- ✅ MR sorting (latest first)
- ✅ Complete comment extraction (including code comments with file/line info)
- ✅ Automatic image download from comments
- ✅ Image viewer with thumbnail display
- ✅ AI-powered best practices extraction via Vertafore API
- ✅ Custom LLM prompts (editable in prompts/extract_best_practices.txt)
- ✅ User-friendly desktop GUI
- ✅ Export functionality
- ✅ Error handling and validation
- ✅ Threaded operations (non-blocking UI)
- ✅ Multiple view modes (all comments, code comments, summary, review, best practices)
- ✅ Secure file-based token storage
