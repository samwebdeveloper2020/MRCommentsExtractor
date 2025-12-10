"""
LLM Service for extracting best practices from code review comments
Supports multiple LLM providers with a unified interface
"""

import requests
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple

class LLMService:
    def __init__(self, api_key: str, provider: str = "vertafore"):
        """Initialize LLM service
        
        Args:
            api_key (str): API key for the Vertafore API
            provider (str): LLM provider ("vertafore", "openai", "anthropic", etc.)
        """
        self.api_key = api_key
        self.provider = provider.lower()
        self.vertafore_api_url = "https://api.dev.env.apps.vertafore.com/shirley/v1/PLATFORM-ADMIN-WEB-UI/VERTAFORE/entities/VERTAFORE/conversations"
        
        # Load prompt template from file
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file"""
        try:
            # Get the project root directory
            current_dir = Path(__file__).parent.parent
            prompt_file = current_dir / "prompts" / "extract_best_practices.txt"
            
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # Fallback to default prompt if file doesn't exist
                return self._get_default_prompt()
        except Exception as e:
            print(f"Error loading prompt template: {e}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Return default prompt if template file is not available"""
        return """You are analyzing GitLab merge request review comments to extract ONLY the coding standards and best practices that are EXPLICITLY mentioned in these specific comments.

CRITICAL INSTRUCTIONS:
- Extract ONLY what is directly stated in the review comments below
- Do NOT add general best practices or common knowledge
- Do NOT infer or assume anything beyond what reviewers explicitly mentioned
- Focus on actionable, specific feedback that was actually given
- Keep each point concise (1-2 sentences maximum)
- If a comment doesn't contain a clear best practice, skip it

OUTPUT FORMAT:
Return a numbered list of specific coding standards mentioned in the reviews. Each item should:
1. Quote or reference the actual review comment
2. State the coding standard briefly
3. Be directly traceable to the review comments

=== REVIEW COMMENTS TO ANALYZE ===
{comments}

=== EXTRACTED CODING STANDARDS (ONLY FROM ABOVE COMMENTS) ===
"""
        
    def extract_best_practices(self, review_comments: List[Dict]) -> Tuple[bool, str]:
        """Extract best practices and code standards from review comments
        
        Args:
            review_comments (List[Dict]): List of review comment discussions
            
        Returns:
            Tuple[bool, str]: (success, extracted_practices or error_message)
        """
        try:
            # Consolidate all comments into a single text
            consolidated_comments = self._consolidate_comments(review_comments)
            
            if not consolidated_comments.strip():
                return False, "No review comments found to analyze"
            
            # Create prompt for LLM
            prompt = self._create_extraction_prompt(consolidated_comments)
            
            # Send to LLM based on provider
            if self.provider == "vertafore":
                return self._call_vertafore_api(prompt)
            elif self.provider == "openai":
                return self._call_openai(prompt)
            elif self.provider == "anthropic":
                return self._call_anthropic(prompt)
            else:
                return False, f"Unsupported LLM provider: {self.provider}"
                
        except Exception as e:
            return False, f"Error extracting best practices: {str(e)}"
    
    def _consolidate_comments(self, review_comments: List[Dict]) -> str:
        """Consolidate review comments into a single text block"""
        consolidated = []
        
        for discussion in review_comments:
            discussion_text = f"\\n=== Discussion {discussion.get('id', 'N/A')} ===\\n"
            
            # Add file context if available
            if discussion.get('position') and discussion['position'].get('new_path'):
                file_path = discussion['position']['new_path']
                line_number = discussion['position'].get('new_line', 'N/A')
                discussion_text += f"File: {file_path}, Line: {line_number}\\n"
            
            # Add all notes in the discussion
            notes = discussion.get('notes', [])
            for i, note in enumerate(notes):
                author = note.get('author', {}).get('name', 'Unknown')
                body = note.get('body', '')
                discussion_text += f"\\nComment {i+1} by {author}:\\n{body}\\n"
            
            # Add code context if available
            if discussion.get('code_context'):
                discussion_text += f"\\nCode Context:\\n{discussion['code_context']}\\n"
            
            consolidated.append(discussion_text)
        
        return "\\n".join(consolidated)
    
    def _call_vertafore_api(self, prompt: str) -> Tuple[bool, str]:
        """Call Vertafore custom API for LLM interactions"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Vertafore API payload structure
            data = {
                "conversationName": "GitLab MR Best Practices Extraction",
                "entityId": "VERTAFORE",
                "tenantId": "VERTAFORE",
                "useCaseName": "CHATBOT",
                "useCaseVersion": "0.0.1",
                "serviceProfileName": "CLAUDE-SONNET-3.5",
                "serviceProfileVersion": "0.0.1",
                "currentMessage": {
                    "content": [
                        {
                            "text": prompt
                        }
                    ],
                    "role": "user"
                },
                "serviceUseParameters": {}
            }
            
            response = requests.post(
                self.vertafore_api_url,
                headers=headers,
                json=data,
                timeout=60  # Longer timeout for custom API
            )
            
            # Accept both 200 (OK) and 201 (Created) as success
            if response.status_code in [200, 201]:
                result = response.json()
                # Parse new Vertafore API response format
                try:
                    # New response structure: content.currentMessage.content[].text
                    content_obj = result.get('content', {})
                    current_message = content_obj.get('currentMessage', {})
                    message_content = current_message.get('content', [])
                    
                    if message_content and len(message_content) > 0:
                        # Extract text from the first content item
                        text_response = message_content[0].get('text', '')
                        if text_response:
                            content = text_response
                        else:
                            content = str(result)
                    else:
                        # Fallback to old structure for compatibility
                        if 'currentMessage' in result and 'content' in result['currentMessage']:
                            content_items = result['currentMessage']['content']
                            if content_items and len(content_items) > 0 and 'text' in content_items[0]:
                                content = content_items[0]['text']
                            else:
                                content = str(result)
                        elif 'response' in result:
                            content = result['response']
                        elif 'message' in result:
                            content = result['message']
                        else:
                            # Final fallback: try to extract any text content
                            content = str(result)
                            
                except (KeyError, IndexError, TypeError) as e:
                    # If parsing fails, return the raw result with error info
                    content = f"Response parsing failed: {str(e)}. Raw response: {str(result)}"
                    
                return True, content
            else:
                return False, f"Vertafore API error: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            return False, "Vertafore API request timed out. Please try again."
        except Exception as e:
            return False, f"Vertafore API call failed: {str(e)}"
    
    def _create_extraction_prompt(self, comments: str) -> str:
        """Create a prompt for extracting best practices from comments"""
        # Use the loaded template and replace {comments} placeholder
        return self.prompt_template.replace("{comments}", comments)
    
    def _call_openai(self, prompt: str) -> Tuple[bool, str]:
        """Call OpenAI API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 1500,
                'temperature': 0.3
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return True, content
            else:
                return False, f"OpenAI API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"OpenAI API call failed: {str(e)}"
    
    def _call_anthropic(self, prompt: str) -> Tuple[bool, str]:
        """Call Anthropic Claude API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 1500,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                return True, content
            else:
                return False, f"Anthropic API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"Anthropic API call failed: {str(e)}"