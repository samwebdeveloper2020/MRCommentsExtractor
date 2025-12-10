"""
SharePoint/Teams Excel Service for exporting coding standards
Supports Microsoft Graph API integration for direct Excel file updates
"""

import re
import requests
import json
from pathlib import Path


class SharePointService:
    """Service for interacting with SharePoint/Teams Excel files via Microsoft Graph API"""
    
    def __init__(self):
        """Initialize SharePoint service with Graph API credentials"""
        self.graph_api_base = "https://graph.microsoft.com/v1.0"
        self.token = self._load_graph_token()
    
    def _load_graph_token(self):
        """Load Microsoft Graph API token from file"""
        token_file = Path("graph_token.json")
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    data = json.load(f)
                    return data.get('token')
            except Exception as e:
                print(f"Error loading Graph token: {e}")
        return None
    
    def _parse_sharepoint_url(self, url):
        """Parse SharePoint/Teams URL to extract site, drive, and file information
        
        Args:
            url: SharePoint or Teams file URL
            
        Returns:
            dict with site_id, drive_id, item_id or None if parsing fails
        """
        # Patterns for various SharePoint/Teams URL formats
        # Teams format: https://company.sharepoint.com/:x:/r/teams/teamname/_layouts/15/Doc2.aspx?sourcedoc={guid}
        # SharePoint direct: https://company.sharepoint.com/sites/sitename/Shared%20Documents/file.xlsx
        
        url_info = {}
        
        # Extract tenant from URL
        tenant_match = re.search(r'https://([^.]+)\.sharepoint\.com', url)
        if tenant_match:
            url_info['tenant'] = tenant_match.group(1)
        
        # Extract document ID from sourcedoc parameter (Teams/SharePoint share links)
        doc_id_match = re.search(r'sourcedoc=%7B([^}%]+)%7D', url)
        if not doc_id_match:
            doc_id_match = re.search(r'sourcedoc=\{([^}]+)\}', url)
        
        if doc_id_match:
            url_info['pattern_type'] = 'sharepoint_docid'
            url_info['doc_id'] = doc_id_match.group(1)
            print(f"DEBUG: Found document ID: {url_info['doc_id']}")
        
        # Extract Teams site name from /teams/ path
        teams_match = re.search(r'/teams/([^/]+)', url)
        if teams_match:
            url_info['site_type'] = 'teams'
            url_info['site_name'] = teams_match.group(1)
            print(f"DEBUG: Found Teams site: {url_info['site_name']}")
        
        # Extract SharePoint site name from /sites/ path
        site_match = re.search(r'/sites/([^/]+)', url)
        if site_match:
            url_info['site_type'] = 'sharepoint'
            url_info['site_name'] = site_match.group(1)
            print(f"DEBUG: Found SharePoint site: {url_info['site_name']}")
        
        return url_info if url_info else None
    
    def _get_file_metadata(self, url_info):
        """Get file metadata from Graph API using URL information
        
        Args:
            url_info: Parsed URL information
            
        Returns:
            tuple: (success, data) where data contains drive_id and item_id
        """
        if not self.token:
            return False, "No Graph API token found. Please configure graph_token.json"
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # If we have a document ID, use it directly to get the item
            if 'doc_id' in url_info:
                doc_id = url_info['doc_id']
                print(f"DEBUG: Searching for file with ID: {doc_id}")
                
                # First, try to get the file directly by ID
                # Graph API can search across all drives using the item ID
                search_url = f"{self.graph_api_base}/me/drive/items/{doc_id}"
                response = requests.get(search_url, headers=headers)
                
                if response.status_code == 200:
                    item_data = response.json()
                    drive_id = item_data.get('parentReference', {}).get('driveId')
                    item_id = item_data.get('id')
                    
                    if drive_id and item_id:
                        print(f"DEBUG: Found file - drive_id: {drive_id}, item_id: {item_id}")
                        return True, {
                            'drive_id': drive_id,
                            'item_id': item_id,
                            'url_info': url_info
                        }
                
                # If direct access fails, try searching by document ID
                print("DEBUG: Direct access failed, trying search...")
                
                # Try to get site information first if available
                if 'tenant' in url_info and 'site_name' in url_info:
                    if url_info.get('site_type') == 'teams':
                        # For Teams sites, use /teams/ path
                        site_url = f"{self.graph_api_base}/sites/{url_info['tenant']}.sharepoint.com:/teams/{url_info['site_name']}"
                    else:
                        # For SharePoint sites, use /sites/ path
                        site_url = f"{self.graph_api_base}/sites/{url_info['tenant']}.sharepoint.com:/sites/{url_info['site_name']}"
                    
                    print(f"DEBUG: Getting site info from: {site_url}")
                    site_response = requests.get(site_url, headers=headers)
                    
                    if site_response.status_code == 200:
                        site_data = site_response.json()
                        site_id = site_data.get('id')
                        print(f"DEBUG: Found site_id: {site_id}")
                        
                        # Get drives for this site
                        drives_url = f"{self.graph_api_base}/sites/{site_id}/drives"
                        drives_response = requests.get(drives_url, headers=headers)
                        
                        if drives_response.status_code == 200:
                            drives = drives_response.json().get('value', [])
                            print(f"DEBUG: Found {len(drives)} drives")
                            
                            # Search in each drive for the document
                            for drive in drives:
                                drive_id = drive['id']
                                
                                # Try to get item by ID from this drive
                                item_url = f"{self.graph_api_base}/drives/{drive_id}/items/{doc_id}"
                                item_response = requests.get(item_url, headers=headers)
                                
                                if item_response.status_code == 200:
                                    print(f"DEBUG: Found file in drive: {drive_id}")
                                    return True, {
                                        'drive_id': drive_id,
                                        'item_id': doc_id,
                                        'url_info': url_info
                                    }
            
            return False, f"Could not locate file. URL info: {url_info}"
            
        except Exception as e:
            print(f"DEBUG: Exception in _get_file_metadata: {str(e)}")
            return False, f"Error accessing Graph API: {str(e)}"
    
    def export_to_excel(self, excel_url, data_rows):
        """Export data to SharePoint/Teams Excel file
        
        Args:
            excel_url: SharePoint or Teams Excel file URL
            data_rows: List of rows to write, each row is a list of cell values
            
        Returns:
            tuple: (success, message)
        """
        # Check if token exists
        if not self.token:
            return False, (
                "Microsoft Graph API token not configured.\n\n"
                "To enable direct SharePoint/Teams export:\n"
                "1. Register an app in Azure AD\n"
                "2. Grant Files.ReadWrite.All permission\n"
                "3. Create graph_token.json with your access token:\n"
                '   {"token": "your-access-token-here"}\n\n'
                "For now, you can export to a local file and upload manually."
            )
        
        # Parse the URL
        url_info = self._parse_sharepoint_url(excel_url)
        if not url_info:
            return False, (
                "Could not parse the SharePoint/Teams URL.\n\n"
                "Supported URL formats:\n"
                "- SharePoint: https://tenant.sharepoint.com/sites/sitename/.../file.xlsx\n"
                "- Teams: https://teams.microsoft.com/...\n"
                "- OneDrive: https://onedrive.live.com/...\n\n"
                "Please check the URL and try again."
            )
        
        # Get file metadata
        success, metadata = self._get_file_metadata(url_info)
        if not success:
            return False, metadata
        
        # Write data to Excel via Graph API
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            drive_id = metadata['drive_id']
            item_id = metadata['item_id']
            
            print(f"DEBUG: Using drive_id: {drive_id}, item_id: {item_id}")
            
            # Create a session to work with the Excel file
            session_url = f"{self.graph_api_base}/drives/{drive_id}/items/{item_id}/workbook/createSession"
            session_data = {"persistChanges": True}
            session_response = requests.post(session_url, headers=headers, json=session_data)
            
            if session_response.status_code == 201:
                session_id = session_response.json().get('id')
                headers['workbook-session-id'] = session_id
                print(f"DEBUG: Created workbook session: {session_id}")
            
            # Get worksheets
            worksheet_url = f"{self.graph_api_base}/drives/{drive_id}/items/{item_id}/workbook/worksheets"
            ws_response = requests.get(worksheet_url, headers=headers)
            
            if ws_response.status_code == 200:
                worksheets = ws_response.json().get('value', [])
                print(f"DEBUG: Found {len(worksheets)} worksheets")
                
                if worksheets:
                    # Use first worksheet or find "Coding Standards" sheet
                    sheet_name = None
                    for ws in worksheets:
                        if 'Coding Standards' in ws.get('name', ''):
                            sheet_name = ws['name']
                            break
                    
                    if not sheet_name:
                        sheet_name = worksheets[0]['name']
                    
                    print(f"DEBUG: Using worksheet: {sheet_name}")
                    
                    # Update range with new data
                    num_rows = len(data_rows)
                    range_address = f"A1:A{num_rows}"
                    
                    # Update the range
                    update_url = f"{self.graph_api_base}/drives/{drive_id}/items/{item_id}/workbook/worksheets('{sheet_name}')/range(address='{range_address}')"
                    update_data = {
                        "values": data_rows
                    }
                    
                    print(f"DEBUG: Updating range {range_address} with {num_rows} rows")
                    update_response = requests.patch(update_url, headers=headers, json=update_data)
                    
                    if update_response.status_code in [200, 201]:
                        print("DEBUG: Successfully updated Excel file")
                        
                        # Close the session
                        if 'workbook-session-id' in headers:
                            close_url = f"{self.graph_api_base}/drives/{drive_id}/items/{item_id}/workbook/closeSession"
                            requests.post(close_url, headers=headers)
                        
                        return True, f"Successfully updated {num_rows} rows in worksheet '{sheet_name}'"
                    else:
                        error_msg = f"Failed to update Excel: {update_response.status_code} - {update_response.text}"
                        print(f"DEBUG: {error_msg}")
                        return False, error_msg
            else:
                error_msg = f"Failed to get worksheets: {ws_response.status_code} - {ws_response.text}"
                print(f"DEBUG: {error_msg}")
                return False, error_msg
            
        except Exception as e:
            print(f"DEBUG: Exception in export_to_excel: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"Error writing to Excel: {str(e)}"
