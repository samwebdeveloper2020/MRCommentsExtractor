"""
Main GUI Window for GitLab MR Comments Viewer
Provides a user-friendly interface to extract and view merge request comments
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import os
from services.gitlab_api import GitLabAPI
from services.llm_service import LLMService
from utils.helpers import parse_gitlab_url, format_datetime, count_comments, extract_comment_text, get_file_info_from_position, extract_images_from_text, replace_images_in_text, get_code_context_from_discussion
from utils.token_manager import TokenManager
from utils.image_viewer import ImageViewer

class MainWindow:
    def __init__(self, root):
        """Initialize the main window
        
        Args:
            root: Tkinter root window
        """
        print("DEBUG: MainWindow __init__ called")
        self.root = root
        self.root.title("GitLab MR Comments Viewer")
        self.root.geometry("1000x700")
        
        # Variables
        self.token_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.project_var = tk.StringVar()
        self.mr_var = tk.StringVar()
        self.mr_state_var = tk.StringVar()
        self.comments_data = None
        self.downloaded_images = {}
        self.projects_data = []
        self.all_project_names = []  # Store all project names for filtering
        self.current_mrs = []
        self.all_mr_names = []  # Store all MR names for filtering
        self.is_filtering = False  # Flag to prevent recursive filtering
        self.is_filtering_mrs = False  # Flag to prevent recursive MR filtering
        
        # Initialize token manager and image viewer
        self.token_manager = TokenManager()
        self.image_viewer = ImageViewer(root)
        
        self.setup_ui()
        self.load_saved_token()
        self.load_saved_llm_token()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
        # Access Token section
        ttk.Label(main_frame, text="GitLab Personal Access Token:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        token_frame = ttk.Frame(main_frame)
        token_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        token_frame.columnconfigure(0, weight=1)
        
        self.token_entry = ttk.Entry(token_frame, textvariable=self.token_var, show="*", width=40)
        self.token_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(token_frame, text="Test", command=self.test_token).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(token_frame, text="Save", command=self.save_token).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(token_frame, text="Clear", command=self.clear_token).grid(row=0, column=3)
        
        # LLM API Key section
        ttk.Label(main_frame, text="Vertafore API Key:").grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        llm_frame = ttk.Frame(main_frame)
        llm_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 5))
        llm_frame.columnconfigure(0, weight=1)
        
        self.llm_token_var = tk.StringVar()
        self.llm_token_entry = ttk.Entry(llm_frame, textvariable=self.llm_token_var, width=50, show="*")
        self.llm_token_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(llm_frame, text="Save API Key", command=self.save_llm_token).grid(row=0, column=1, padx=(5, 0))
        ttk.Button(llm_frame, text="Clear API Key", command=self.clear_llm_token).grid(row=0, column=2, padx=(5, 0))
        
        # Project selection section
        ttk.Label(main_frame, text="Select Project:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        project_frame = ttk.Frame(main_frame)
        project_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        project_frame.columnconfigure(0, weight=1)
        
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(project_frame, textvariable=self.project_var, width=50)
        self.project_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.project_combo.bind('<<ComboboxSelected>>', self.on_project_selected)
        self.project_combo.bind('<KeyRelease>', self.filter_projects_on_type)
        self.project_combo.bind('<FocusIn>', self.on_project_focus_in)
        # Remove the Button-1 binding that was interfering with typing
        
        ttk.Button(project_frame, text="Load Projects", command=self.load_projects).grid(row=0, column=1)
        
        # MR filters section
        ttk.Label(main_frame, text="MR Filter:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        filter_frame = ttk.Frame(main_frame)
        filter_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.mr_state_var = tk.StringVar(value="opened")
        ttk.Label(filter_frame, text="State:").pack(side=tk.LEFT, padx=(0, 5))
        state_combo = ttk.Combobox(filter_frame, textvariable=self.mr_state_var, width=15, state="readonly")
        state_combo['values'] = ("all", "opened", "closed", "merged")
        state_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(filter_frame, text="Load MRs", command=self.load_merge_requests).pack(side=tk.LEFT, padx=(0, 5))
        
        # MR selection section
        ttk.Label(main_frame, text="Select MR:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        mr_frame = ttk.Frame(main_frame)
        mr_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        mr_frame.columnconfigure(0, weight=1)
        
        self.mr_var = tk.StringVar()
        self.mr_combo = ttk.Combobox(mr_frame, textvariable=self.mr_var, width=50)
        self.mr_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.mr_combo.bind('<KeyRelease>', self.filter_mrs_on_type)
        self.mr_combo.bind('<FocusIn>', self.on_mr_focus_in)
        self.mr_combo.bind('<<ComboboxSelected>>', self.on_mr_selected)
        # Remove the Button-1 binding that was interfering with typing
        
        # Alternative: MR URL section
        ttk.Label(main_frame, text="Or Enter MR URL:").grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Buttons section
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.fetch_button = ttk.Button(button_frame, text="Fetch Comments", command=self.fetch_comments)
        self.fetch_button.grid(row=0, column=0, padx=(0, 10))
        
        self.export_button = ttk.Button(button_frame, text="Export to JSON", command=self.export_comments, state="disabled")
        self.export_button.grid(row=0, column=1, padx=(0, 10))
        
        self.images_button = ttk.Button(button_frame, text="View Images", command=self.view_images, state="disabled")
        self.images_button.grid(row=0, column=2, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear", command=self.clear_results).grid(row=0, column=3)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Results section with notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: All Comments
        self.all_comments_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.all_comments_frame, text="All Comments")
        self.setup_comments_tab(self.all_comments_frame, "all")
        
        # Tab 2: Code Comments
        self.code_comments_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.code_comments_frame, text="Code Comments")
        self.setup_comments_tab(self.code_comments_frame, "code")
        
        # Tab 3: Comments Review
        self.comments_review_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.comments_review_frame, text="Comments Review")
        self.setup_comments_review_tab()
        
        # Tab 4: Best Practices
        self.best_practices_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.best_practices_frame, text="Best Practices")
        self.setup_best_practices_tab()
        
        # Tab 5: Summary
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Summary")
        self.setup_summary_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_comments_tab(self, parent, tab_type):
        """Setup a comments display tab
        
        Args:
            parent: Parent frame
            tab_type: Type of tab ('all' or 'code')
        """
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
        # Text widget with scrollbar
        text_widget = scrolledtext.ScrolledText(parent, wrap=tk.WORD, width=80, height=30)
        text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Store reference
        if tab_type == "all":
            self.all_comments_text = text_widget
        else:
            self.code_comments_text = text_widget
            
    def setup_comments_review_tab(self):
        """Setup the comments review tab with checkboxes for each discussion"""
        self.comments_review_frame.columnconfigure(0, weight=1)
        self.comments_review_frame.rowconfigure(1, weight=1)
        
        # Control frame for buttons
        control_frame = ttk.Frame(self.comments_review_frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Button(control_frame, text="Check All", command=self.check_all_comments).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Uncheck All", command=self.uncheck_all_comments).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Export Checked", command=self.export_checked_comments).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Extract Best Practices", command=self.extract_best_practices).pack(side=tk.LEFT, padx=(0, 5))
        
        # Scrollable frame for comment blocks
        self.review_canvas = tk.Canvas(self.comments_review_frame)
        self.review_scrollbar = ttk.Scrollbar(self.comments_review_frame, orient="vertical", command=self.review_canvas.yview)
        self.review_scrollable_frame = ttk.Frame(self.review_canvas)
        
        self.review_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.review_canvas.configure(scrollregion=self.review_canvas.bbox("all"))
        )
        
        self.review_canvas.create_window((0, 0), window=self.review_scrollable_frame, anchor="nw")
        self.review_canvas.configure(yscrollcommand=self.review_scrollbar.set)
        
        self.review_canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0), pady=5)
        self.review_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S), pady=5)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            self.review_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.review_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store checkbox variables
        self.comment_checkboxes = {}
        
    def setup_summary_tab(self):
        """Setup the summary tab"""
        self.summary_frame.columnconfigure(0, weight=1)
        self.summary_frame.rowconfigure(0, weight=1)
        
        self.summary_text = scrolledtext.ScrolledText(self.summary_frame, wrap=tk.WORD, width=80, height=30)
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
    def test_token(self):
        """Test the GitLab access token"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter your GitLab Personal Access Token")
            return
            
        def test_in_thread():
            self.progress.start()
            self.status_var.set("Testing token...")
            
            try:
                api = GitLabAPI(token)
                success, message = api.test_connection()
                
                if success:
                    messagebox.showinfo("Success", message)
                    self.status_var.set("Token validated successfully")
                else:
                    messagebox.showerror("Error", message)
                    self.status_var.set("Token validation failed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to test token: {str(e)}")
                self.status_var.set("Token test failed")
            finally:
                self.progress.stop()
        
        threading.Thread(target=test_in_thread, daemon=True).start()
        
    def fetch_comments(self):
        """Fetch comments from the merge request"""
        token = self.token_var.get().strip()
        url = self.url_var.get().strip()
        
        if not token:
            messagebox.showerror("Error", "Please enter your GitLab Personal Access Token")
            return
            
        if not url:
            messagebox.showerror("Error", "Please enter the Merge Request URL")
            return
        
        # Parse URL
        success, project_id, mr_iid, error = parse_gitlab_url(url)
        if not success:
            messagebox.showerror("Error", f"Invalid URL: {error}")
            return
            
        def fetch_in_thread():
            self.progress.start()
            self.fetch_button.config(state="disabled")
            self.status_var.set("Fetching comments...")
            
            try:
                api = GitLabAPI(token)
                success, data, numeric_project_id = api.get_merge_request_discussions(project_id, mr_iid)
                
                if success:
                    # Store references for code context fetching
                    self.current_api = api
                    self.current_project_id = project_id
                    self.comments_data = data
                    
                    # Download images from comments
                    self.status_var.set("Downloading images...")
                    self.downloaded_images = api.extract_images_from_comments(data, project_numeric_id=numeric_project_id)
                    
                    # Display comments with images
                    self.display_comments(data)
                    self.export_button.config(state="normal")
                    
                    # Enable images button if we have images
                    if self.downloaded_images:
                        self.images_button.config(state="normal")
                        self.status_var.set(f"Fetched {len(data)} discussions with {len(self.downloaded_images)} images")
                    else:
                        self.status_var.set(f"Fetched {len(data)} discussions successfully")
                else:
                    messagebox.showerror("Error", f"Failed to fetch comments: {data}")
                    self.status_var.set("Failed to fetch comments")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                self.status_var.set("Error occurred")
            finally:
                self.progress.stop()
                self.fetch_button.config(state="normal")
        
        threading.Thread(target=fetch_in_thread, daemon=True).start()
        
    def display_comments(self, discussions):
        """Display comments in the UI
        
        Args:
            discussions: List of discussion objects from GitLab API
        """
        # Clear existing content
        self.all_comments_text.delete(1.0, tk.END)
        self.code_comments_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        
        # Clear comments review tab
        for widget in self.review_scrollable_frame.winfo_children():
            widget.destroy()
        self.comment_checkboxes.clear()
        
        # Count comments
        counts = count_comments(discussions)
        
        # Display all comments
        all_comments_content = f"Total Discussions: {len(discussions)}\n"
        all_comments_content += f"Total Comments: {counts['total']}\n\n"
        all_comments_content += "="*80 + "\n\n"
        
        code_comments_content = f"Code Comments: {counts['code']}\n\n"
        code_comments_content += "="*80 + "\n\n"
        
        for i, discussion in enumerate(discussions, 1):
            notes = discussion.get('notes', [])
            
            # Skip empty discussions or system notes only
            user_notes = [note for note in notes if not note.get('system', False)]
            if not user_notes:
                continue
                
            discussion_header = f"Discussion #{i}\n"
            discussion_header += f"ID: {discussion.get('id', 'N/A')}\n"
            
            # Check if this is a code comment
            is_code_comment = False
            position_info = ""
            
            # Check discussion position or note positions
            if discussion.get('position') or any(note.get('position') for note in user_notes):
                is_code_comment = True
                
                # Get position info from first note with position
                for note in user_notes:
                    if note.get('position'):
                        file_info = get_file_info_from_position(note['position'])
                        if file_info:
                            position_info = f"File: {file_info['file_path']}\n"
                            if file_info['line_number']:
                                position_info += f"Line: {file_info['line_number']}\n"
                        break
            
            discussion_content = discussion_header + position_info + "\n"
            
            # Add notes
            for note in user_notes:
                author = note.get('author', {}).get('name', 'Unknown')
                created_at = format_datetime(note.get('created_at', ''))
                body = extract_comment_text(note)
                
                note_content = f"Author: {author}\n"
                note_content += f"Date: {created_at}\n"
                
                # Check for images in this comment
                image_urls = extract_images_from_text(body)
                if image_urls:
                    note_content += f"Images: {len(image_urls)} image(s) found\n"
                
                note_content += f"Comment:\n{body}\n"
                
                # Add image information
                if image_urls:
                    note_content += "\nImages in this comment:\n"
                    for img_url in image_urls:
                        if img_url in self.downloaded_images:
                            local_path = self.downloaded_images[img_url]
                            note_content += f"  • {os.path.basename(local_path)} (downloaded)\n"
                        else:
                            note_content += f"  • {img_url} (download failed)\n"
                
                note_content += "-" * 40 + "\n"
                
                discussion_content += note_content
            
            discussion_content += "=" * 80 + "\n\n"
            
            # Add to all comments
            all_comments_content += discussion_content
            
            # Add to code comments if applicable
            if is_code_comment:
                code_comments_content += discussion_content
        
        # Update text widgets
        self.all_comments_text.insert(tk.END, all_comments_content)
        self.code_comments_text.insert(tk.END, code_comments_content)
        
        # Create summary
        summary_content = f"MERGE REQUEST COMMENTS SUMMARY\n"
        summary_content += "=" * 50 + "\n\n"
        summary_content += f"Total Discussions: {len(discussions)}\n"
        summary_content += f"Total Comments: {counts['total']}\n"
        summary_content += f"Code Comments: {counts['code']}\n"
        summary_content += f"General Comments: {counts['general']}\n"
        summary_content += f"Downloaded Images: {len(self.downloaded_images)}\n\n"
        
        # Add author breakdown
        authors = {}
        for discussion in discussions:
            for note in discussion.get('notes', []):
                if not note.get('system', False):
                    author = note.get('author', {}).get('name', 'Unknown')
                    authors[author] = authors.get(author, 0) + 1
        
        if authors:
            summary_content += "Comments by Author:\n"
            summary_content += "-" * 20 + "\n"
            for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True):
                summary_content += f"{author}: {count} comments\n"
        
        # Add image information to summary
        if self.downloaded_images:
            summary_content += "\nDownloaded Images:\n"
            summary_content += "-" * 20 + "\n"
            for i, (url, local_path) in enumerate(self.downloaded_images.items(), 1):
                summary_content += f"{i}. {os.path.basename(local_path)}\n"
        
        self.summary_text.insert(tk.END, summary_content)
        
        # Populate comments review tab
        self.populate_comments_review(discussions)
        
    def populate_comments_review(self, discussions):
        """Populate the comments review tab with checkboxes for each discussion
        
        Args:
            discussions: List of discussion objects from GitLab API
        """
        discussion_count = 0
        
        for i, discussion in enumerate(discussions):
            notes = discussion.get('notes', [])
            
            # Skip empty discussions or system notes only
            user_notes = [note for note in notes if not note.get('system', False)]
            if not user_notes:
                continue
                
            discussion_count += 1
            
            # Create frame for this discussion block
            discussion_frame = ttk.LabelFrame(self.review_scrollable_frame, 
                                            text=f"Discussion {discussion_count}", 
                                            padding="10")
            discussion_frame.pack(fill="x", padx=5, pady=5)
            
            # Create checkbox variable and checkbox
            var = tk.BooleanVar()
            discussion_id = discussion.get('id', f'discussion_{i}')
            self.comment_checkboxes[discussion_id] = var
            
            checkbox_frame = ttk.Frame(discussion_frame)
            checkbox_frame.pack(fill="x", pady=(0, 10))
            
            checkbox = ttk.Checkbutton(checkbox_frame, 
                                     text=f"Export Discussion {discussion_count} to Comments Repo", 
                                     variable=var)
            checkbox.pack(side=tk.LEFT)
            
            # Add discussion info
            info_frame = ttk.Frame(discussion_frame)
            info_frame.pack(fill="x", pady=(0, 10))
            
            # Check if this is a code comment and get code context
            is_code_comment = False
            position_info = ""
            code_context = None
            
            file_info = get_code_context_from_discussion(discussion)
            if file_info and file_info.get('file_path') != 'Unknown file':
                is_code_comment = True
                position_info = f"📁 File: {file_info['file_path']}"
                if file_info.get('line_number'):
                    position_info += f" (Line {file_info['line_number']})"
                    
                    # Fetch code context from GitLab
                    if hasattr(self, 'current_api') and hasattr(self, 'current_project_id'):
                        try:
                            success, lines_data = self.current_api.get_file_lines_around(
                                self.current_project_id, 
                                file_info['file_path'], 
                                file_info['line_number'],
                                context_lines=3
                            )
                            if success:
                                code_context = lines_data
                        except Exception as e:
                            print(f"Error fetching code context: {e}")
            
            # Add info labels
            if is_code_comment:
                ttk.Label(info_frame, text="💻 Code Comment", foreground="blue").pack(side=tk.LEFT, padx=(0, 10))
            else:
                ttk.Label(info_frame, text="💬 General Comment", foreground="green").pack(side=tk.LEFT, padx=(0, 10))
            
            if position_info:
                ttk.Label(info_frame, text=position_info, foreground="gray").pack(side=tk.LEFT)
            
            # Add code context if available
            if code_context:
                code_frame = ttk.LabelFrame(discussion_frame, text="📄 Code Context", padding="5")
                code_frame.pack(fill="x", pady=(5, 10))
                
                # Create text widget for code display
                code_text = tk.Text(code_frame, wrap=tk.NONE, height=len(code_context['lines']) + 1, 
                                  width=100, font=("Consolas", 9), relief="sunken", borderwidth=1)
                code_text.pack(fill="x", padx=5, pady=5)
                
                # Add horizontal scrollbar for long lines
                code_scrollbar = ttk.Scrollbar(code_frame, orient="horizontal", command=code_text.xview)
                code_text.configure(xscrollcommand=code_scrollbar.set)
                code_scrollbar.pack(fill="x", padx=5)
                
                # Configure text tags for highlighting
                code_text.tag_configure("target_line", background="#ffeb3b", foreground="#000")
                code_text.tag_configure("line_number", foreground="#666", font=("Consolas", 8))
                code_text.tag_configure("code_content", font=("Consolas", 9))
                
                # Insert code lines
                for line_data in code_context['lines']:
                    line_num = line_data['number']
                    content = line_data['content']
                    is_target = line_data['is_target']
                    
                    # Format line number (right-aligned in 4 characters)
                    line_num_str = f"{line_num:4d}: "
                    code_text.insert(tk.END, line_num_str, "line_number")
                    
                    # Insert code content
                    if is_target:
                        code_text.insert(tk.END, content + "\n", ("code_content", "target_line"))
                    else:
                        code_text.insert(tk.END, content + "\n", "code_content")
                
                code_text.config(state="disabled")  # Make read-only
            
            # Add comments in this discussion
            for note_idx, note in enumerate(user_notes):
                author = note.get('author', {}).get('name', 'Unknown')
                created_at = format_datetime(note.get('created_at', ''))
                body = extract_comment_text(note)
                
                # Create frame for this comment
                comment_frame = ttk.Frame(discussion_frame)
                comment_frame.pack(fill="x", pady=5)
                
                # Author and date header
                header = f"👤 {author} • 📅 {created_at}"
                header_label = ttk.Label(comment_frame, text=header, font=("TkDefaultFont", 9, "bold"))
                header_label.pack(anchor="w")
                
                # Comment body
                comment_text = tk.Text(comment_frame, wrap=tk.WORD, height=4, width=80, 
                                     relief="groove", borderwidth=1, padx=5, pady=5)
                comment_text.pack(fill="x", pady=(5, 0))
                comment_text.insert("1.0", body)
                comment_text.config(state="disabled")  # Make read-only
                
                # Check for images in this comment
                image_urls = extract_images_from_text(body)
                if image_urls:
                    image_label = ttk.Label(comment_frame, 
                                          text=f"🖼️ {len(image_urls)} image(s) attached", 
                                          foreground="purple")
                    image_label.pack(anchor="w", pady=(2, 0))
                
                # Add separator between comments (except for last comment)
                if note_idx < len(user_notes) - 1:
                    separator = ttk.Separator(discussion_frame, orient='horizontal')
                    separator.pack(fill="x", pady=(5, 0))
        
    def export_comments(self):
        """Export comments to JSON file"""
        if not self.comments_data:
            messagebox.showerror("Error", "No comments data to export")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save comments as JSON"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.comments_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Comments exported to {filename}")
                self.status_var.set(f"Exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
                self.status_var.set("Export failed")
    
    def view_images(self):
        """Open image viewer window to display downloaded images"""
        if not self.downloaded_images:
            messagebox.showinfo("No Images", "No images were found in the comments.")
            return
        
        image_paths = list(self.downloaded_images.values())
        self.image_viewer.create_image_display_window(
            image_paths, 
            f"Images from Merge Request Comments ({len(image_paths)} images)"
        )
    
    def check_all_comments(self):
        """Check all comment checkboxes"""
        for var in self.comment_checkboxes.values():
            var.set(True)
    
    def uncheck_all_comments(self):
        """Uncheck all comment checkboxes"""
        for var in self.comment_checkboxes.values():
            var.set(False)
    
    def export_checked_comments(self):
        """Export only the checked comments to JSON"""
        if not self.comments_data:
            messagebox.showerror("Error", "No comments data to export")
            return
        
        # Get checked discussions
        checked_discussions = []
        for discussion_id, var in self.comment_checkboxes.items():
            if var.get():
                # Find the discussion in comments_data
                for discussion in self.comments_data:
                    if discussion.get('id') == discussion_id:
                        checked_discussions.append(discussion)
                        break
        
        if not checked_discussions:
            messagebox.showwarning("Warning", "No comments are checked for export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save checked comments as JSON"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(checked_discussions, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Checked comments exported to {filename}")
                self.status_var.set(f"Exported {len(checked_discussions)} checked discussions")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
                self.status_var.set("Export failed")
    
    def clear_results(self):
        """Clear all results and reset the interface"""
        self.all_comments_text.delete(1.0, tk.END)
        self.code_comments_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        
        # Clear comments review tab
        for widget in self.review_scrollable_frame.winfo_children():
            widget.destroy()
        self.comment_checkboxes.clear()
        
        self.comments_data = None
        self.downloaded_images = {}
        self.current_api = None
        self.current_project_id = None
        self.export_button.config(state="disabled")
        self.images_button.config(state="disabled")
        self.status_var.set("Results cleared")
    
    def load_saved_token(self):
        """Load saved token from file if it exists"""
        token, gitlab_url, success = self.token_manager.load_token()
        if success and token:
            self.token_var.set(token)
            self.status_var.set("Token loaded from saved file")
        else:
            self.status_var.set("No saved token found")
    
    def save_token(self):
        """Save the current token to file"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter a token to save")
            return
        
        success = self.token_manager.save_token(token)
        if success:
            messagebox.showinfo("Success", "Token saved successfully!")
            self.status_var.set("Token saved to local file")
        else:
            messagebox.showerror("Error", "Failed to save token")
            self.status_var.set("Failed to save token")
    
    def clear_token(self):
        """Clear the token from both UI and saved file"""
        result = messagebox.askyesno("Confirm", "This will clear the token from the interface and delete the saved token file. Continue?")
        if result:
            self.token_var.set("")
            success = self.token_manager.delete_token()
            if success:
                messagebox.showinfo("Success", "Token cleared and saved file deleted")
                self.status_var.set("Token cleared")
            else:
                messagebox.showwarning("Warning", "Token cleared from interface, but failed to delete saved file")
                self.status_var.set("Token cleared (file deletion failed)")
    
    def test_button_click(self):
        """Test function to verify button works"""
        print("DEBUG: Button clicked! This confirms the button is working")
        messagebox.showinfo("Test", "Button is working! Now calling load_projects...")
        self.load_projects()
    
    def test_button_click(self):
        """Test method to verify button clicks work"""
        print("DEBUG: test_button_click called!")
        with open("debug.log", "a") as f:
            f.write("DEBUG: test_button_click called!\n")
        messagebox.showinfo("Test", "Button click works!")
        
    def load_projects(self):
        """Load user's projects from GitLab API"""
        print("DEBUG: load_projects called")
        token = self.token_var.get().strip()
        if not token:
            print("DEBUG: No token provided, showing warning")
            messagebox.showwarning("Warning", "Please enter your GitLab Personal Access Token first")
            return
        
        def load_in_thread():
            self.progress.start()
            self.status_var.set("Loading Certificate-forms platform projects...")
            
            try:
                api = GitLabAPI(token)
                success, projects = api.get_user_projects()
                
                print(f"DEBUG: API call result - success: {success}")
                if success:
                    print(f"DEBUG: Found {len(projects) if projects else 0} projects")
                    self.status_var.set(f"Processing {len(projects)} projects...")
                    # Convert GitLab projects to our format
                    self.projects_data = []
                    for proj in projects:
                        project_data = {
                            'name': proj.get('name', 'Unknown'),
                            'path': proj.get('path_with_namespace', ''),
                            'description': proj.get('description', ''),
                            'id': proj.get('id'),
                            'web_url': proj.get('web_url', ''),
                            'last_activity_at': proj.get('last_activity_at', ''),
                            'visibility': proj.get('visibility', 'private')
                        }
                        self.projects_data.append(project_data)
                    
                    # Create display names
                    project_names = []
                    for proj in self.projects_data:
                        # Format: "Project Name (path) - visibility"
                        name = f"{proj['name']} ({proj['path']}) - {proj['visibility']}"
                        project_names.append(name)
                    
                    self.all_project_names = project_names.copy()
                    self.project_combo['values'] = project_names
                    # Enable typing in combobox for search
                    self.project_combo['state'] = 'normal'
                    
                    if project_names:
                        self.status_var.set(f"Loaded {len(project_names)} Certificate-forms platform projects")
                    else:
                        self.status_var.set("No Certificate-forms platform projects found")
                else:
                    messagebox.showerror("Error", f"Failed to load Certificate-forms projects: {projects}")
                    self.status_var.set("Failed to load Certificate-forms projects")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                self.status_var.set("Error loading Certificate-forms projects")
            finally:
                self.progress.stop()
        
        print("DEBUG: Starting thread")
        threading.Thread(target=load_in_thread, daemon=True).start()
    
    def filter_projects_on_type(self, event=None):
        """Filter projects as user types in the combobox"""
        if self.is_filtering:
            return
            
        self.is_filtering = True
        try:
            current_text = self.project_var.get().lower()
            
            if not current_text:
                # Show all projects if search is empty
                filtered_projects = self.all_project_names
            else:
                # Filter projects that contain the search text
                filtered_projects = [
                    name for name in self.all_project_names 
                    if current_text in name.lower()
                ]
            
            # Update combobox values without forcing dropdown open
            self.project_combo['values'] = filtered_projects
                
        finally:
            self.is_filtering = False
    
    def on_project_focus_in(self, event=None):
        """Handle project combobox focus to show all projects if none are filtered"""
        if not self.project_combo['values'] and self.all_project_names:
            self.project_combo['values'] = self.all_project_names
    
    def filter_mrs_on_type(self, event=None):
        """Filter MRs as user types in the combobox"""
        if self.is_filtering_mrs:
            return
            
        self.is_filtering_mrs = True
        try:
            current_text = self.mr_var.get().lower()
            
            if not current_text:
                # Show all MRs if search is empty
                filtered_mrs = self.all_mr_names
            else:
                # Filter MRs that contain the search text
                filtered_mrs = [
                    name for name in self.all_mr_names 
                    if current_text in name.lower()
                ]
            
            # Update combobox values without forcing dropdown open
            self.mr_combo['values'] = filtered_mrs
                
        finally:
            self.is_filtering_mrs = False
    
    def on_mr_focus_in(self, event=None):
        """Handle MR combobox focus to show all MRs if none are filtered"""
        if not self.mr_combo['values'] and self.all_mr_names:
            self.mr_combo['values'] = self.all_mr_names
    
    def on_project_selected(self, event=None):
        """Handle project selection"""
        selected = self.project_combo.current()
        if selected >= 0 and selected < len(self.projects_data):
            project = self.projects_data[selected]
            self.status_var.set(f"Selected: {project['name']}")
            # Clear MR selection and search data when project changes
            self.mr_combo.set('')
            self.mr_combo['values'] = []
            self.all_mr_names = []
            self.current_mrs = []
            self.mr_combo['state'] = 'readonly'
    
    def load_merge_requests(self):
        """Load merge requests for the selected project"""
        selected = self.project_combo.current()
        if selected < 0 or selected >= len(self.projects_data):
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter your GitLab Personal Access Token")
            return
        
        project = self.projects_data[selected]
        project_path = project['path']
        mr_state = self.mr_state_var.get()
        
        def load_in_thread():
            self.progress.start()
            self.status_var.set(f"Loading {mr_state} merge requests from {project['name']}...")
            
            try:
                api = GitLabAPI(token)
                success, mrs = api.get_merge_requests(project_path, state=mr_state)
                
                if success:
                    self.current_mrs = mrs
                    mr_options = []
                    
                    for mr in mrs:
                        title = mr.get('title', 'No title')
                        iid = mr.get('iid', 'N/A')
                        state = mr.get('state', 'unknown')
                        author = mr.get('author', {}).get('name', 'Unknown')
                        created_at = mr.get('created_at', '')
                        updated_at = mr.get('updated_at', '')
                        
                        # Format date (prefer created_at for consistency)
                        try:
                            if created_at:
                                date_part = created_at.split('T')[0]
                            elif updated_at:
                                date_part = updated_at.split('T')[0]
                            else:
                                date_part = 'N/A'
                        except:
                            date_part = 'N/A'
                        
                        # Create display text with creation date for better chronological sorting
                        display_text = f"MR!{iid} - {title} ({state}) - {author} - {date_part}"
                        mr_options.append(display_text)
                    
                    self.all_mr_names = mr_options.copy()
                    self.mr_combo['values'] = mr_options
                    # Enable typing in combobox for search
                    self.mr_combo['state'] = 'normal'
                    self.status_var.set(f"Loaded {len(mrs)} {mr_state} merge requests")
                else:
                    messagebox.showerror("Error", f"Failed to load MRs: {mrs}")
                    self.status_var.set("Failed to load merge requests")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                self.status_var.set("Error loading merge requests")
            finally:
                self.progress.stop()
        
        threading.Thread(target=load_in_thread, daemon=True).start()
    
    def on_mr_selected(self, event=None):
        """Handle MR selection"""
        selected = self.mr_combo.current()
        if selected >= 0 and selected < len(self.current_mrs):
            mr = self.current_mrs[selected]
            project = self.projects_data[self.project_combo.current()]
            
            # Construct GitLab URL
            mr_url = f"https://gitlab.com/{project['path']}/-/merge_requests/{mr['iid']}"
            self.url_var.set(mr_url)
            
            self.status_var.set(f"Selected MR!{mr['iid']}: {mr['title']}")
    
    def fetch_comments(self):
        """Fetch comments from the merge request"""
        token = self.token_var.get().strip()
        url = self.url_var.get().strip()
        
        if not token:
            messagebox.showerror("Error", "Please enter your GitLab Personal Access Token")
            return
        
        if not url:
            # Check if we have a selected MR
            if self.mr_combo.current() >= 0:
                self.on_mr_selected()  # Update URL from selected MR
                url = self.url_var.get().strip()
            
            if not url:
                messagebox.showerror("Error", "Please select an MR from dropdown or enter MR URL")
                return
        
        # Parse URL
        success, project_id, mr_iid, error = parse_gitlab_url(url)
        if not success:
            messagebox.showerror("Error", f"Invalid URL: {error}")
            return
            
        def fetch_in_thread():
            self.progress.start()
            self.fetch_button.config(state="disabled")
            self.status_var.set("Fetching comments...")
            
            try:
                api = GitLabAPI(token)
                success, data, numeric_project_id = api.get_merge_request_discussions(project_id, mr_iid)
                
                if success:
                    # Store references for code context fetching
                    self.current_api = api
                    self.current_project_id = project_id
                    
                    self.comments_data = data
                    
                    # Download images from comments
                    self.status_var.set("Downloading images...")
                    self.downloaded_images = api.extract_images_from_comments(data, project_numeric_id=numeric_project_id)
                    
                    # Display comments with images
                    self.display_comments(data)
                    self.export_button.config(state="normal")
                    
                    # Enable images button if we have images
                    if self.downloaded_images:
                        self.images_button.config(state="normal")
                        self.status_var.set(f"Fetched {len(data)} discussions with {len(self.downloaded_images)} images")
                    else:
                        self.status_var.set(f"Fetched {len(data)} discussions successfully")
                else:
                    messagebox.showerror("Error", f"Failed to fetch comments: {data}")
                    self.status_var.set("Failed to fetch comments")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                self.status_var.set("Error occurred")
            finally:
                self.progress.stop()
                self.fetch_button.config(state="normal")
        
        threading.Thread(target=fetch_in_thread, daemon=True).start()
    
    def save_llm_token(self):
        """Save Vertafore API token to file"""
        token = self.llm_token_var.get().strip()
        if not token:
            messagebox.showwarning("Warning", "Please enter your Vertafore API key")
            return
            
        success = self.token_manager.save_llm_token(token)
        if success:
            messagebox.showinfo("Success", "Vertafore API key saved successfully")
            self.status_var.set("Vertafore API key saved")
        else:
            messagebox.showerror("Error", "Failed to save Vertafore API key")
            self.status_var.set("Failed to save Vertafore API key")
    
    def clear_llm_token(self):
        """Clear Vertafore API token from interface and file"""
        self.llm_token_var.set("")
        success = self.token_manager.delete_llm_token()
        if success:
            messagebox.showinfo("Success", "Vertafore API key cleared")
            self.status_var.set("Vertafore API key cleared")
        else:
            messagebox.showwarning("Warning", "Vertafore API key cleared from interface, but failed to delete saved file")
            self.status_var.set("Vertafore API key cleared (file deletion failed)")
    
    def load_saved_llm_token(self):
        """Load saved Vertafore token from file if it exists"""
        token = self.token_manager.load_llm_token()
        if token:
            self.llm_token_var.set(token)
            self.status_var.set("Vertafore API key loaded from saved file")
    
    def setup_best_practices_tab(self):
        """Setup the best practices tab"""
        # Main scrollable text area
        self.best_practices_text = scrolledtext.ScrolledText(
            self.best_practices_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=25,
            font=('Consolas', 10)
        )
        self.best_practices_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initially show instructions
        instructions = """Extract Best Practices from Review Comments

Instructions:
1. Go to the 'Comments Review' tab
2. Check the discussions you want to analyze
3. Click 'Extract Best Practices' button
4. Make sure you have set your Vertafore API key in the main interface

The AI (Claude Sonnet 3.5 via Vertafore API) will analyze the selected review comments and extract:
• Code quality standards
• Best practices for coding
• Security considerations
• Performance recommendations
• Maintainability guidelines
• Testing practices
• Documentation standards

Using Vertafore's enterprise AI platform for secure, compliant analysis.
"""
        self.best_practices_text.insert(tk.END, instructions)
        self.best_practices_text.config(state=tk.DISABLED)
    
    def extract_best_practices(self):
        """Extract best practices from checked review comments using Vertafore AI"""
        # Get Vertafore API token
        llm_token = self.llm_token_var.get().strip()
        if not llm_token:
            messagebox.showwarning("Warning", "Please enter your Vertafore API key first")
            return
        
        # Get checked discussions
        checked_discussions = []
        for discussion_id, checkbox_var in self.comment_checkboxes.items():
            if checkbox_var.get():
                # Find the discussion in comments_data
                for discussion in self.comments_data:
                    if discussion.get('id') == discussion_id:
                        checked_discussions.append(discussion)
                        break
        
        if not checked_discussions:
            messagebox.showwarning("Warning", "Please check at least one discussion in the Comments Review tab")
            return
        
        def extract_in_thread():
            self.progress.start()
            self.status_var.set("Extracting best practices with Vertafore AI...")
            
            try:
                # Initialize Vertafore LLM service
                llm_service = LLMService(llm_token, provider="vertafore")
                
                # Extract best practices
                success, result = llm_service.extract_best_practices(checked_discussions)
                
                if success:
                    # Update the best practices tab
                    self.best_practices_text.config(state=tk.NORMAL)
                    self.best_practices_text.delete(1.0, tk.END)
                    
                    # Add header
                    header = f"Best Practices Extracted from {len(checked_discussions)} Review Discussions\n"
                    header += f"Generated by Claude Sonnet 3.5 via Vertafore Enterprise AI\n"
                    header += "=" * 70 + "\n\n"
                    self.best_practices_text.insert(tk.END, header)
                    
                    # Add extracted practices
                    self.best_practices_text.insert(tk.END, result)
                    
                    self.best_practices_text.config(state=tk.DISABLED)
                    
                    # Switch to best practices tab
                    self.notebook.select(self.best_practices_frame)
                    
                    self.status_var.set(f"Successfully extracted best practices from {len(checked_discussions)} discussions")
                else:
                    messagebox.showerror("Error", f"Failed to extract best practices: {result}")
                    self.status_var.set("Failed to extract best practices")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                self.status_var.set("Error extracting best practices")
            finally:
                self.progress.stop()
        
        threading.Thread(target=extract_in_thread, daemon=True).start()