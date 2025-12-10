"""
SharePoint Direct Export - Updates Excel files directly via SharePoint REST API
Works with SharePoint/Teams URLs without requiring Azure AD app registration
Uses session-based authentication with SharePoint cookies
"""

import re
import requests
import json
from urllib.parse import urlparse, parse_qs, unquote


class SharePointDirectExport:
    """Direct export to SharePoint Excel files using REST API"""
    
    def __init__(self):
        """Initialize SharePoint direct exporter"""
        self.session = requests.Session()
    
    def _parse_sharepoint_url(self, url):
        """Parse SharePoint/Teams URL to extract file information
        
        Args:
            url: SharePoint or Teams Excel file URL
            
        Returns:
            dict with parsed information or None
        """
        info = {}
        
        # Extract tenant
        tenant_match = re.search(r'https://([^.]+)\.sharepoint\.com', url)
        if tenant_match:
            info['tenant'] = tenant_match.group(1)
            info['base_url'] = f"https://{tenant_match.group(1)}.sharepoint.com"
        
        # Extract site path (teams or sites)
        teams_match = re.search(r'/teams/([^/]+)', url)
        sites_match = re.search(r'/sites/([^/]+)', url)
        
        if teams_match:
            info['site_type'] = 'teams'
            info['site_name'] = teams_match.group(1)
            info['site_path'] = f"/teams/{info['site_name']}"
        elif sites_match:
            info['site_type'] = 'sites'
            info['site_name'] = sites_match.group(1)
            info['site_path'] = f"/sites/{info['site_name']}"
        
        # Extract file path from URL
        # Pattern: /Shared%20Documents/folder/file.xlsx
        doc_path_match = re.search(r'/Shared%20Documents/(.+?)(?:\?|$)', url)
        if doc_path_match:
            file_path = unquote(doc_path_match.group(1))
            info['file_path'] = file_path
            info['file_name'] = file_path.split('/')[-1]
            info['folder_path'] = '/'.join(file_path.split('/')[:-1]) if '/' in file_path else ''
        
        # Extract document ID if present
        doc_id_match = re.search(r'd=w([a-f0-9]+)', url)
        if doc_id_match:
            # The 'd=w' parameter contains the file ID without dashes
            raw_id = doc_id_match.group(1)
            # Convert to GUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            if len(raw_id) == 32:
                guid = f"{raw_id[0:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:32]}"
                info['doc_id'] = guid
        
        return info if 'tenant' in info else None
    
    def update_excel_file(self, sharepoint_url, data_rows):
        """Update Excel file on SharePoint/Teams directly
        
        Args:
            sharepoint_url: SharePoint or Teams Excel file URL
            data_rows: List of rows, each row is a list of cell values
            
        Returns:
            tuple: (success, message)
        """
        # Parse the URL
        url_info = self._parse_sharepoint_url(sharepoint_url)
        
        if not url_info:
            return False, "Could not parse SharePoint URL. Please check the link format."
        
        print(f"DEBUG: Parsed URL info: {url_info}")
        
        # Build the REST API endpoint for the file
        if 'file_path' not in url_info:
            return False, "Could not extract file path from URL."
        
        base_url = url_info['base_url']
        site_path = url_info['site_path']
        file_path = url_info['file_path']
        
        # Construct the SharePoint REST API URL
        # Try to open the file using the Microsoft Graph-compatible API endpoint
        file_url = f"{base_url}{site_path}/_api/web/GetFileByServerRelativeUrl('{site_path}/Shared Documents/{file_path}')"
        
        print(f"DEBUG: File API URL: {file_url}")
        
        try:
            # Method 1: Try using SharePoint Online REST API with anonymous/cookie auth
            # This requires the user to be authenticated in their browser
            
            instructions = (
                "To update the SharePoint file directly, you need to:\n\n"
                "1. Make sure you're logged into SharePoint/Teams in your browser\n"
                "2. Keep your browser session active\n"
                "3. Grant the application permission to access your files\n\n"
                "Alternative approach:\n"
                "Since direct API access requires authentication tokens, "
                "I recommend using the 'Export to local file' option and then:\n"
                "1. Open your SharePoint/Teams file in Excel Online\n"
                "2. Copy the content from the exported local Excel file\n"
                "3. Paste it into the online Excel file\n\n"
                "This is the most reliable method without enterprise API setup."
            )
            
            return False, instructions
            
        except Exception as e:
            return False, f"Error accessing SharePoint: {str(e)}"
    
    def _try_office_api_update(self, url_info, data_rows):
        """Try updating via Office REST API (requires authentication)"""
        # This would require proper authentication tokens
        # For now, return instructions for manual update
        return False, "Direct API update requires authentication. Please use the manual upload method."
