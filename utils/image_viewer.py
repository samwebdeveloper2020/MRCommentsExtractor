"""
Image viewer utilities for displaying images in the GUI
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

class ImageViewer:
    def __init__(self, parent):
        """Initialize image viewer
        
        Args:
            parent: Parent tkinter widget
        """
        self.parent = parent
        self.image_references = []  # Keep references to prevent garbage collection
        
    def create_image_display_window(self, image_paths, title="Images from Comments"):
        """Create a window to display images
        
        Args:
            image_paths (list): List of image file paths
            title (str): Window title
        """
        if not image_paths:
            return
            
        # Create new window
        img_window = tk.Toplevel(self.parent)
        img_window.title(title)
        img_window.geometry("800x600")
        
        # Create scrollable frame
        canvas = tk.Canvas(img_window)
        scrollbar = ttk.Scrollbar(img_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add images to scrollable frame
        for i, image_path in enumerate(image_paths):
            self.add_image_to_frame(scrollable_frame, image_path, i)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def add_image_to_frame(self, frame, image_path, index):
        """Add an image to the scrollable frame
        
        Args:
            frame: Frame to add image to
            image_path (str): Path to image file
            index (int): Image index for labeling
        """
        try:
            if not os.path.exists(image_path):
                return
                
            # Create frame for this image
            img_frame = ttk.LabelFrame(frame, text=f"Image {index + 1}: {os.path.basename(image_path)}")
            img_frame.pack(fill="x", padx=10, pady=5)
            
            # Load and resize image
            with Image.open(image_path) as pil_image:
                # Resize if too large
                max_width, max_height = 750, 400
                pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                
                # Keep reference to prevent garbage collection
                self.image_references.append(photo)
                
                # Create label with image
                img_label = ttk.Label(img_frame, image=photo)
                img_label.pack(padx=10, pady=10)
                
                # Add image info
                info_text = f"Size: {pil_image.size[0]}x{pil_image.size[1]} pixels"
                info_label = ttk.Label(img_frame, text=info_text)
                info_label.pack(pady=(0, 10))
                
        except Exception as e:
            # Create error label if image can't be loaded
            error_frame = ttk.LabelFrame(frame, text=f"Image {index + 1}: Error")
            error_frame.pack(fill="x", padx=10, pady=5)
            
            error_label = ttk.Label(error_frame, text=f"Failed to load image: {str(e)}")
            error_label.pack(padx=10, pady=10)
            
    def add_inline_image_to_text(self, text_widget, image_path, max_width=300):
        """Add an inline image to a text widget
        
        Args:
            text_widget: tkinter Text widget
            image_path (str): Path to image file
            max_width (int): Maximum width for inline image
        """
        try:
            if not os.path.exists(image_path):
                text_widget.insert(tk.END, f"[Image not found: {image_path}]\n")
                return
                
            # Load and resize image for inline display
            with Image.open(image_path) as pil_image:
                # Calculate new size maintaining aspect ratio
                width, height = pil_image.size
                if width > max_width:
                    ratio = max_width / width
                    new_width = max_width
                    new_height = int(height * ratio)
                    pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                
                # Keep reference
                self.image_references.append(photo)
                
                # Insert image into text widget
                text_widget.image_create(tk.END, image=photo)
                text_widget.insert(tk.END, f"\n[{os.path.basename(image_path)}]\n\n")
                
        except Exception as e:
            text_widget.insert(tk.END, f"[Error loading image {os.path.basename(image_path)}: {str(e)}]\n\n")