"""
Utility helper functions for the GitLab MR Comments Viewer
"""

import re
from datetime import datetime

def parse_gitlab_url(url):
    """Parse GitLab MR URL to extract project and MR ID
    
    Args:
        url (str): GitLab merge request URL
        
    Returns:
        tuple: (success: bool, project_id: str, mr_iid: int, error_message: str)
    """
    try:
        # Pattern to match GitLab MR URLs
        pattern = r'https?://([^/]+)/(.+?)/-/merge_requests/(\d+)'
        match = re.match(pattern, url.strip())
        
        if not match:
            return False, None, None, "Invalid GitLab MR URL format"
        
        gitlab_host = match.group(1)
        project_path = match.group(2)
        mr_iid = int(match.group(3))
        
        return True, project_path, mr_iid, None
        
    except Exception as e:
        return False, None, None, f"Error parsing URL: {str(e)}"

def format_datetime(iso_string):
    """Format ISO datetime string to readable format
    
    Args:
        iso_string (str): ISO formatted datetime string
        
    Returns:
        str: Formatted datetime string
    """
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        return iso_string

def count_comments(discussions):
    """Count total comments in discussions
    
    Args:
        discussions (list): List of discussion objects
        
    Returns:
        dict: Dictionary with comment counts
    """
    total_comments = 0
    code_comments = 0
    general_comments = 0
    
    for discussion in discussions:
        notes = discussion.get('notes', [])
        for note in notes:
            if note.get('system', False):
                continue  # Skip system notes
            
            total_comments += 1
            
            # Check if it's a code comment (has position info)
            if note.get('position') or discussion.get('position'):
                code_comments += 1
            else:
                general_comments += 1
    
    return {
        'total': total_comments,
        'code': code_comments,
        'general': general_comments
    }

def extract_comment_text(note):
    """Extract clean comment text from note
    
    Args:
        note (dict): Note object from GitLab API
        
    Returns:
        str: Clean comment text
    """
    body = note.get('body', '')
    # Remove GitLab markdown for mentions, etc.
    # This is a basic cleanup - could be enhanced
    return body.strip()

def get_file_info_from_position(position):
    """Extract file information from position object
    
    Args:
        position (dict): Position object from GitLab API
        
    Returns:
        dict: File information
    """
    if not position:
        return None
    
    return {
        'file_path': position.get('new_path') or position.get('old_path', 'Unknown file'),
        'line_number': position.get('new_line') or position.get('old_line'),
        'line_type': position.get('line_range', {}).get('start', {}).get('type', 'unknown'),
        'base_sha': position.get('base_sha'),
        'head_sha': position.get('head_sha'),
        'start_sha': position.get('start_sha')
    }

def get_code_context_from_discussion(discussion):
    """Extract code context information from a discussion
    
    Args:
        discussion (dict): Discussion object from GitLab API
        
    Returns:
        dict: Code context information or None
    """
    # Check discussion position first
    if discussion.get('position'):
        return get_file_info_from_position(discussion['position'])
    
    # Check notes for position information
    for note in discussion.get('notes', []):
        if note.get('position'):
            return get_file_info_from_position(note['position'])
    
    return None

def extract_images_from_text(text):
    """Extract image URLs from comment text
    
    Args:
        text (str): Comment text that may contain images
        
    Returns:
        list: List of image URLs found in the text
    """
    image_urls = []
    
    # Pattern for markdown images: ![alt](url)
    markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    # Pattern for HTML img tags: <img src="url" ... >
    html_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    
    # Find markdown images
    for match in re.finditer(markdown_pattern, text):
        url = match.group(2)
        if url and is_image_url(url):
            image_urls.append(url)
    
    # Find HTML images
    for match in re.finditer(html_pattern, text):
        url = match.group(1)
        if url and is_image_url(url):
            image_urls.append(url)
    
    return image_urls

def is_image_url(url):
    """Check if URL points to an image
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if URL appears to be an image
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
    url_lower = url.lower()
    
    # Check if URL ends with image extension
    for ext in image_extensions:
        if ext in url_lower:
            return True
    
    # GitLab upload URLs typically contain 'uploads' and look like images
    if 'uploads' in url_lower and any(ext in url_lower for ext in image_extensions):
        return True
        
    return False

def replace_images_in_text(text, image_map):
    """Replace image URLs in text with local file references
    
    Args:
        text (str): Original text with image URLs
        image_map (dict): Dictionary mapping URLs to local file paths
        
    Returns:
        str: Text with image URLs replaced by local file references
    """
    result_text = text
    
    for original_url, local_path in image_map.items():
        # Replace in markdown format
        result_text = result_text.replace(f']({original_url})', f']({local_path})')
        
        # Replace in HTML format
        result_text = result_text.replace(f'src="{original_url}"', f'src="{local_path}"')
        result_text = result_text.replace(f"src='{original_url}'", f"src='{local_path}'")
    
    return result_text