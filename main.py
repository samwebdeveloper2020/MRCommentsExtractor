"""
GitLab MR Comments Viewer - Desktop Application
Main entry point for the application
"""

import tkinter as tk
from gui.main_window import MainWindow

def main():
    """Initialize and run the application"""
    try:
        print("DEBUG: Starting main application")
        root = tk.Tk()
        print("DEBUG: Tkinter root created")
        app = MainWindow(root)
        print("DEBUG: MainWindow created, starting mainloop")
        root.mainloop()
        print("DEBUG: Application closed")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()