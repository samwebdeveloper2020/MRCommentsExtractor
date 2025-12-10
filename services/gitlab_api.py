"""
GitLab API Service
Handles all GitLab API interactions for merge request comments
"""

import requests
from urllib.parse import quote, urljoin, urlparse
import json
import os
import re
from pathlib import Path

class GitLabAPI:
    def __init__(self, token, base_url="https://gitlab.com"):
        """Initialize GitLab API client
        
        Args:
            token (str): Personal Access Token for GitLab
            base_url (str): Base URL for GitLab instance
        """
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Private-Token': token,
            'Content-Type': 'application/json'
        }
        
    def get_project_info(self, project_path):
        """Get project information including numeric ID
        
        Args:
            project_path (str): GitLab project path (e.g., 'owner/repo')
            
        Returns:
            tuple: (success: bool, project_data: dict or error_message: str)
        """
        try:
            encoded_project = quote(project_path, safe='')
            url = f"{self.base_url}/api/v4/projects/{encoded_project}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                return False, "Authentication failed. Please check your access token."
            elif response.status_code == 404:
                return False, "Project not found. Please check the project path."
            else:
                return False, f"API request failed with status {response.status_code}: {response.text}"
                
        except Exception as e:
            return False, f"Error getting project info: {str(e)}"

    def get_merge_request_discussions(self, project_id, mr_iid):
        """Get all discussions (comments) for a merge request
        
        Args:
            project_id (str): GitLab project ID (URL encoded)
            mr_iid (int): Merge request internal ID
            
        Returns:
            tuple: (success: bool, data: list or error_message: str, project_numeric_id: int or None)
        """
        try:
            # First get project info to get numeric ID
            project_success, project_data = self.get_project_info(project_id)
            if not project_success:
                return False, project_data, None
            
            numeric_project_id = project_data.get('id')
            
            # URL encode the project_id
            encoded_project = quote(project_id, safe='')
            url = f"{self.base_url}/api/v4/projects/{encoded_project}/merge_requests/{mr_iid}/discussions"
            
            all_discussions = []
            page = 1
            
            while True:
                params = {
                    'page': page,
                    'per_page': 100  # Maximum per page
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    discussions = response.json()
                    if not discussions:  # No more discussions
                        break
                    all_discussions.extend(discussions)
                    page += 1
                elif response.status_code == 401:
                    return False, "Authentication failed. Please check your access token.", None
                elif response.status_code == 403:
                    return False, "Access forbidden. You may not have permission to view this merge request.", None
                elif response.status_code == 404:
                    return False, "Merge request not found. Please check the URL.", None
                else:
                    return False, f"API request failed with status {response.status_code}: {response.text}", None
            
            return True, all_discussions, numeric_project_id
            
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}", None
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", None
    
    def test_connection(self):
        """Test if the token and connection are working
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            url = f"{self.base_url}/api/v4/user"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Connected successfully as {user_data.get('name', 'Unknown User')}"
            elif response.status_code == 401:
                return False, "Invalid access token"
            else:
                return False, f"Connection failed: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def get_file_content(self, project_id, file_path, ref="HEAD"):
        """Get file content from GitLab repository
        
        Args:
            project_id (str): GitLab project ID (URL encoded)
            file_path (str): Path to the file in the repository
            ref (str): Git reference (branch, tag, commit SHA)
            
        Returns:
            tuple: (success: bool, content: str or error_message: str)
        """
        try:
            encoded_project = quote(project_id, safe='')
            encoded_file_path = quote(file_path, safe='')
            url = f"{self.base_url}/api/v4/projects/{encoded_project}/repository/files/{encoded_file_path}/raw"
            
            params = {'ref': ref}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return True, response.text
            elif response.status_code == 404:
                return False, f"File not found: {file_path}"
            elif response.status_code == 401:
                return False, "Authentication failed for file access"
            elif response.status_code == 403:
                return False, "Access forbidden for file content"
            else:
                return False, f"Failed to get file content: HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Error getting file content: {str(e)}"
    
    def get_file_lines_around(self, project_id, file_path, line_number, context_lines=5, ref="HEAD"):
        """Get lines around a specific line number from a file
        
        Args:
            project_id (str): GitLab project ID
            file_path (str): Path to the file
            line_number (int): Target line number
            context_lines (int): Number of lines before and after to include
            ref (str): Git reference
            
        Returns:
            tuple: (success: bool, lines_data: dict or error_message: str)
        """
        try:
            success, content = self.get_file_content(project_id, file_path, ref)
            if not success:
                return False, content
            
            lines = content.splitlines()
            total_lines = len(lines)
            
            if line_number < 1 or line_number > total_lines:
                return False, f"Line number {line_number} is out of range (file has {total_lines} lines)"
            
            # Calculate range (convert to 0-based indexing)
            start_line = max(0, line_number - 1 - context_lines)
            end_line = min(total_lines, line_number + context_lines)
            
            lines_data = {
                'file_path': file_path,
                'target_line': line_number,
                'start_line': start_line + 1,  # Convert back to 1-based
                'end_line': end_line,
                'total_lines': total_lines,
                'lines': []
            }
            
            for i in range(start_line, end_line):
                lines_data['lines'].append({
                    'number': i + 1,
                    'content': lines[i],
                    'is_target': (i + 1) == line_number
                })
            
            return True, lines_data
            
        except Exception as e:
            return False, f"Error getting file lines: {str(e)}"
    
    def get_merge_requests(self, project_path, state="all", per_page=100):
        """Get merge requests from a project
        
        Args:
            project_path (str): GitLab project path (e.g., 'owner/repo')
            state (str): State of MRs to fetch ('opened', 'closed', 'merged', 'all')
            per_page (int): Number of MRs per page
            
        Returns:
            tuple: (success: bool, merge_requests: list or error_message: str)
        """
        try:
            encoded_project = quote(project_path, safe='')
            url = f"{self.base_url}/api/v4/projects/{encoded_project}/merge_requests"
            
            all_mrs = []
            page = 1
            
            while True:
                params = {
                    'state': state,
                    'page': page,
                    'per_page': per_page,
                    'order_by': 'created_at',  # Sort by creation date for consistent chronological order
                    'sort': 'desc'  # Descending order (latest first)
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    mrs = response.json()
                    if not mrs:  # No more MRs
                        break
                    all_mrs.extend(mrs)
                    page += 1
                    
                    # Limit to reasonable number to avoid long loading times
                    if len(all_mrs) >= 500:  # Stop at 500 MRs
                        break
                elif response.status_code == 401:
                    return False, "Authentication failed. Please check your access token."
                elif response.status_code == 404:
                    return False, f"Project not found: {project_path}"
                else:
                    return False, f"API request failed with status {response.status_code}: {response.text}"
            
            # Additional client-side sorting to ensure proper chronological order
            try:
                all_mrs.sort(key=lambda mr: mr.get('created_at', ''), reverse=True)
            except:
                pass  # If sorting fails, return as-is
                
            return True, all_mrs
            
        except Exception as e:
            return False, f"Error getting merge requests: {str(e)}"
    
    def get_merge_request_details(self, project_path, mr_iid):
        """Get detailed information about a specific merge request
        
        Args:
            project_path (str): GitLab project path (e.g., 'owner/repo')
            mr_iid (int): Merge request internal ID
            
        Returns:
            tuple: (success: bool, mr_data: dict or error_message: str)
        """
        try:
            encoded_project = quote(project_path, safe='')
            url = f"{self.base_url}/api/v4/projects/{encoded_project}/merge_requests/{mr_iid}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                return False, "Authentication failed. Please check your access token."
            elif response.status_code == 404:
                return False, f"Merge request !{mr_iid} not found in {project_path}"
            else:
                return False, f"API request failed with status {response.status_code}: {response.text}"
                
        except Exception as e:
            return False, f"Error getting merge request details: {str(e)}"
    
    def get_merge_request_resource_state_events(self, project_path, mr_iid):
        """Get resource state events for a merge request (includes assignee changes)
        
        Args:
            project_path (str): GitLab project path (e.g., 'owner/repo')
            mr_iid (int): Merge request internal ID
            
        Returns:
            tuple: (success: bool, events: list or error_message: str)
        """
        try:
            encoded_project = quote(project_path, safe='')
            url = f"{self.base_url}/api/v4/projects/{encoded_project}/merge_requests/{mr_iid}/resource_state_events"
            
            all_events = []
            page = 1
            
            while True:
                params = {
                    'page': page,
                    'per_page': 100
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    events = response.json()
                    if not events:
                        break
                    all_events.extend(events)
                    page += 1
                elif response.status_code == 401:
                    return False, "Authentication failed. Please check your access token."
                elif response.status_code == 404:
                    return False, f"Merge request !{mr_iid} not found"
                else:
                    return False, f"API request failed with status {response.status_code}: {response.text}"
            
            return True, all_events
            
        except Exception as e:
            return False, f"Error getting resource state events: {str(e)}"
    
    def get_merge_request_notes(self, project_path, mr_iid):
        """Get all notes for a merge request (includes system notes for assignee changes)
        
        Args:
            project_path (str): GitLab project path (e.g., 'owner/repo')
            mr_iid (int): Merge request internal ID
            
        Returns:
            tuple: (success: bool, notes: list or error_message: str)
        """
        try:
            encoded_project = quote(project_path, safe='')
            url = f"{self.base_url}/api/v4/projects/{encoded_project}/merge_requests/{mr_iid}/notes"
            
            all_notes = []
            page = 1
            
            while True:
                params = {
                    'page': page,
                    'per_page': 100,
                    'sort': 'asc',  # Chronological order
                    'order_by': 'created_at'
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    notes = response.json()
                    if not notes:
                        break
                    all_notes.extend(notes)
                    page += 1
                elif response.status_code == 401:
                    return False, "Authentication failed. Please check your access token."
                elif response.status_code == 404:
                    return False, f"Merge request !{mr_iid} not found"
                else:
                    return False, f"API request failed with status {response.status_code}: {response.text}"
            
            return True, all_notes
            
        except Exception as e:
            return False, f"Error getting merge request notes: {str(e)}"
    
    def get_user_projects(self, membership=True, owned=True, starred=True, per_page=100):
        """Get projects accessible to the authenticated user
        
        Args:
            membership (bool): Include projects where user is a member
            owned (bool): Include projects owned by user
            starred (bool): Include starred projects
            per_page (int): Number of projects per page
            
        Returns:
            tuple: (success: bool, projects: list or error_message: str)
        """
        try:
            url = f"{self.base_url}/api/v4/projects"
            
            all_projects = []
            page = 1
            
            while True:
                params = {
                    'page': page,
                    'per_page': 50,  # Smaller page size for faster response
                    'order_by': 'last_activity_at',
                    'sort': 'desc',
                    'simple': False,  # Get full project info
                    'min_access_level': 10,  # Guest level access and above
                    'search': 'certificate'  # Search for projects containing 'certificate'
                }
                
                print(f"DEBUG: Making request to page {page}...")
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                print(f"DEBUG: Response status: {response.status_code}")
                
                if response.status_code == 200:
                    projects = response.json()
                    if projects:
                        print(f"DEBUG: Received {len(projects)} projects on page {page}")
                    if not projects:  # No more projects
                        break
                    # Filter for Certificate-forms-related projects
                    certificate_projects = []
                    for project in projects:
                        project_name = project.get('name', '').lower()
                        project_path = project.get('path_with_namespace', '').lower()
                        project_desc = project.get('description', '').lower() if project.get('description') else ''
                        
                        # Check if project is related to Certificate forms platform
                        if ('certificate-forms' in project_name or 'certificate-forms' in project_path or 
                            'certificate' in project_name or 'certificate' in project_path or
                            'certificate' in project_desc or 'forms' in project_name):
                            certificate_projects.append(project)
                    
                    all_projects.extend(certificate_projects)
                    page += 1
                    
                    # Limit to reasonable number - smaller limit for faster loading
                    if len(all_projects) >= 100:
                        break
                elif response.status_code == 401:
                    return False, "Authentication failed. Please check your access token."
                else:
                    return False, f"API request failed with status {response.status_code}: {response.text}"
            
            print(f"DEBUG: Returning {len(all_projects)} Certificate-forms-related projects")
            return True, all_projects
            
        except requests.exceptions.Timeout:
            print("DEBUG: Request timed out")
            return False, "Request timed out. Please check your internet connection."
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Request exception: {e}")
            return False, f"Network error: {str(e)}"
        except Exception as e:
            print(f"DEBUG: Unexpected exception: {e}")
            return False, f"Error getting user projects: {str(e)}"
    
    def download_image(self, image_url, download_dir="images", project_numeric_id=None):
        """Download an image from GitLab
        
        Args:
            image_url (str): URL of the image to download
            download_dir (str): Directory to save images
            project_numeric_id (int): GitLab numeric project ID for uploads
            
        Returns:
            tuple: (success: bool, local_path: str or error_message: str)
        """
        try:
            # Create images directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
            
            original_url = image_url
            
            # Handle GitLab uploads specially
            if image_url.startswith('/uploads/') and project_numeric_id:
                # Convert old upload format to new GitLab format: /-/project/{id}/uploads/{hash}/{file}
                upload_path = image_url[9:]  # Remove '/uploads/'
                image_url = f"{self.base_url}/-/project/{project_numeric_id}/uploads/{upload_path}"
                print(f"Converted upload URL to: {image_url}")
            elif image_url.startswith(('/-/project/', '/uploads/')) or ('/-/project/' in image_url):
                # This is already a GitLab upload URL - make it absolute
                if image_url.startswith('/'):
                    image_url = urljoin(self.base_url, image_url)
                print(f"GitLab upload URL detected: {image_url}")
            elif image_url.startswith('/'):
                # Handle other relative URLs by making them absolute
                image_url = urljoin(self.base_url, image_url)
            elif not image_url.startswith('http'):
                return False, f"Invalid image URL: {image_url}"
            
            # Get filename from URL
            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            
            # If no filename, generate one based on the original URL
            if not filename or '.' not in filename:
                # Extract extension from original URL if possible
                ext = '.png'  # default
                if '.' in original_url:
                    ext = '.' + original_url.split('.')[-1].split('?')[0]  # Remove query params
                filename = f"image_{abs(hash(image_url)) % 10000}{ext}"
            
            local_path = os.path.join(download_dir, filename)
            
            # Ensure we don't overwrite existing files
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(local_path):
                local_path = os.path.join(download_dir, f"{base_name}_{counter}{ext}")
                counter += 1
            
            print(f"Attempting to download: {image_url}")
            
            # Download the image with authentication
            response = requests.get(image_url, headers=self.headers, stream=True, timeout=30)
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Check if it's actually an image
                content_type = response.headers.get('content-type', '')
                print(f"Content-Type: {content_type}")
                
                if not content_type.startswith('image/'):
                    return False, f"URL does not point to an image (content-type: {content_type})"
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verify file was created and has content
                if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                    return True, local_path
                else:
                    return False, "Downloaded file is empty or was not created"
                    
            elif response.status_code == 404:
                return False, f"Image not found (404): {image_url}"
            elif response.status_code == 403:
                return False, f"Access forbidden (403): May need different permissions"
            elif response.status_code == 401:
                return False, f"Authentication failed (401): Check your token permissions"
            else:
                return False, f"HTTP {response.status_code}: {response.text[:100]}"
                
        except requests.exceptions.Timeout:
            return False, f"Download timeout for {image_url}"
        except requests.exceptions.RequestException as e:
            return False, f"Network error downloading {image_url}: {str(e)}"
        except Exception as e:
            return False, f"Error downloading image: {str(e)}"
    
    def extract_images_from_comments(self, discussions, download_dir="images", project_numeric_id=None):
        """Extract and download images from merge request comments
        
        Args:
            discussions (list): List of discussion objects
            download_dir (str): Directory to save images
            project_numeric_id (int): GitLab numeric project ID for uploads
            
        Returns:
            dict: Dictionary mapping original URLs to local paths
        """
        image_map = {}
        download_results = {}  # Track success/failure for each URL
        
        # Pattern to match markdown images and HTML img tags
        markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        html_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        
        print(f"Starting image extraction from {len(discussions)} discussions...")
        
        try:
            for discussion_idx, discussion in enumerate(discussions):
                for note_idx, note in enumerate(discussion.get('notes', [])):
                    body = note.get('body', '')
                    
                    # Skip if no body or system note
                    if not body or note.get('system', False):
                        continue
                    
                    # Find markdown images
                    markdown_matches = list(re.finditer(markdown_pattern, body))
                    if markdown_matches:
                        print(f"Found {len(markdown_matches)} markdown images in discussion {discussion_idx}, note {note_idx}")
                    
                    for match in markdown_matches:
                        image_url = match.group(2).strip()
                        alt_text = match.group(1)
                        print(f"  Markdown image: {alt_text} -> {image_url}")
                        
                        if image_url not in image_map and image_url not in download_results:
                            success, result = self.download_image(image_url, download_dir, project_numeric_id)
                            download_results[image_url] = (success, result)
                            if success:
                                image_map[image_url] = result
                                print(f"    Successfully downloaded to: {result}")
                            else:
                                print(f"    Download failed: {result}")
                    
                    # Find HTML images
                    html_matches = list(re.finditer(html_pattern, body))
                    if html_matches:
                        print(f"Found {len(html_matches)} HTML images in discussion {discussion_idx}, note {note_idx}")
                    
                    for match in html_matches:
                        image_url = match.group(1).strip()
                        print(f"  HTML image: {image_url}")
                        
                        if image_url not in image_map and image_url not in download_results:
                            success, result = self.download_image(image_url, download_dir, project_numeric_id)
                            download_results[image_url] = (success, result)
                            if success:
                                image_map[image_url] = result
                                print(f"    Successfully downloaded to: {result}")
                            else:
                                print(f"    Download failed: {result}")
                                
        except Exception as e:
            print(f"Error extracting images: {e}")
        
        print(f"Image extraction complete. Successfully downloaded {len(image_map)} images.")
        if download_results:
            failed_count = sum(1 for success, _ in download_results.values() if not success)
            if failed_count > 0:
                print(f"Failed to download {failed_count} images:")
                for url, (success, result) in download_results.items():
                    if not success:
                        print(f"  {url}: {result}")
        
        return image_map