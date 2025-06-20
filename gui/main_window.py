import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
import os
import threading
import subprocess
import time
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import client.client_api as api

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class NgrokManager:
    def __init__(self):
        self.ngrok_process = None
        self.ngrok_url = None
        self.is_running = False
    
    def start_ngrok(self, port=5000):
        """Start ngrok tunnel"""
        try:
            # Kill any existing ngrok processes
            subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
            time.sleep(2)
            
            # Start ngrok
            self.ngrok_process = subprocess.Popen(
                ["ngrok", "http", str(port), "--log=stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ngrok to start and get URL
            time.sleep(3)
            url = self.get_ngrok_url()
            if url:
                self.ngrok_url = url
                self.is_running = True
                return url
            else:
                self.stop_ngrok()
                return None
                
        except Exception as e:
            print(f"Failed to start ngrok: {e}")
            return None
    
    def get_ngrok_url(self):
        """Get ngrok public URL"""
        try:
            # Try to get URL from ngrok API
            import requests
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                tunnels = response.json()
                for tunnel in tunnels.get('tunnels', []):
                    if tunnel.get('proto') == 'https':
                        return tunnel.get('public_url')
            return None
        except:
            return None
    
    def stop_ngrok(self):
        """Stop ngrok tunnel"""
        if self.ngrok_process:
            self.ngrok_process.terminate()
            self.ngrok_process = None
        
        # Kill any remaining ngrok processes
        subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
        
        self.is_running = False
        self.ngrok_url = None

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Central File Server Client")
        self.geometry("800x600")
        
        # Initialize ngrok manager
        self.ngrok_manager = NgrokManager()
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(self, text="File Server Client", 
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Server connection frame
        self.connection_frame = ctk.CTkFrame(self)
        self.connection_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.connection_frame.grid_columnconfigure(1, weight=1)
        
        # Server URL input
        ctk.CTkLabel(self.connection_frame, text="Server URL:").grid(row=0, column=0, padx=10, pady=10)
        
        self.url_entry = ctk.CTkEntry(self.connection_frame, placeholder_text="Enter server URL or use ngrok")
        self.url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.url_entry.insert(0, api.get_server_url())
        
        self.connect_btn = ctk.CTkButton(self.connection_frame, text="Connect", 
                                        command=self.connect_to_server, width=100)
        self.connect_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Ngrok controls
        self.ngrok_btn = ctk.CTkButton(self.connection_frame, text="Start Ngrok", 
                                      command=self.toggle_ngrok, width=100)
        self.ngrok_btn.grid(row=0, column=3, padx=10, pady=10)
        
        self.local_server_btn = ctk.CTkButton(self.connection_frame, text="Use Local", 
                                             command=self.use_local_server, width=100)
        self.local_server_btn.grid(row=0, column=4, padx=10, pady=10)
        
        # File list frame
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.list_frame.grid_rowconfigure(0, weight=1)
        
        # File listbox
        self.file_listbox = ctk.CTkTextbox(self.list_frame, width=700, height=300)
        self.file_listbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        # File operation buttons
        self.refresh_btn = ctk.CTkButton(self.button_frame, text="Refresh List", 
                                        command=self.refresh_files)
        self.refresh_btn.grid(row=0, column=0, padx=10, pady=10)
        
        self.download_btn = ctk.CTkButton(self.button_frame, text="Download File", 
                                         command=self.download_file)
        self.download_btn.grid(row=0, column=1, padx=10, pady=10)
        
        self.upload_btn = ctk.CTkButton(self.button_frame, text="Upload File", 
                                       command=self.upload_file)
        self.upload_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="Ready")
        self.status_label.grid(row=4, column=0, padx=20, pady=10)
        
        # Store file list
        self.file_list = []
        
        # Test initial connection
        self.test_connection()
    
    def toggle_ngrok(self):
        """Start or stop ngrok tunnel"""
        if not self.ngrok_manager.is_running:
            self.start_ngrok_thread()
        else:
            self.stop_ngrok()
    
    def start_ngrok_thread(self):
        """Start ngrok in a separate thread"""
        def start_ngrok():
            self.status_label.configure(text="Starting ngrok tunnel...")
            self.ngrok_btn.configure(text="Starting...", state="disabled")
            
            url = self.ngrok_manager.start_ngrok()
            
            if url:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, url)
                api.set_server_url(url)
                self.status_label.configure(text=f"Ngrok tunnel active: {url}")
                self.ngrok_btn.configure(text="Stop Ngrok", state="normal")
                self.test_connection()
            else:
                self.status_label.configure(text="Failed to start ngrok tunnel")
                self.ngrok_btn.configure(text="Start Ngrok", state="normal")
                messagebox.showerror("Error", "Failed to start ngrok tunnel.\nMake sure ngrok is installed and you have an auth token.")
        
        threading.Thread(target=start_ngrok, daemon=True).start()
    
    def stop_ngrok(self):
        """Stop ngrok tunnel"""
        self.ngrok_manager.stop_ngrok()
        self.ngrok_btn.configure(text="Start Ngrok")
        self.status_label.configure(text="Ngrok tunnel stopped")
        self.use_local_server()
    
    def use_local_server(self):
        """Switch to local server"""
        local_url = "http://localhost:5000"
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, local_url)
        api.set_server_url(local_url)
        self.test_connection()
    
    def connect_to_server(self):
        """Connect to the entered server URL"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a server URL")
            return
        
        api.set_server_url(url)
        self.test_connection()
    
    def test_connection(self):
        """Test connection to server"""
        def test():
            self.status_label.configure(text="Testing connection...")
            
            if api.test_connection():
                self.status_label.configure(text=f"Connected to: {api.get_server_url()}")
                self.refresh_files()
            else:
                self.status_label.configure(text="Failed to connect to server")
                self.file_listbox.delete("0.0", "end")
                self.file_listbox.insert("end", "Cannot connect to server.\nCheck if:\n1. Server is running\n2. URL is correct\n3. Network connection is available")
        
        threading.Thread(target=test, daemon=True).start()
    
    def refresh_files(self):
        """Refresh file list from server"""
        def refresh():
            try:
                self.status_label.configure(text="Refreshing...")
                files = api.list_files()
                self.file_list = files
                
                self.file_listbox.delete("0.0", "end")
                if files:
                    for i, filename in enumerate(files):
                        self.file_listbox.insert("end", f"{i+1}. {filename}\n")
                    self.status_label.configure(text=f"Found {len(files)} files")
                else:
                    self.file_listbox.insert("end", "No files available on server")
                    self.status_label.configure(text="No files found")
                    
            except Exception as e:
                self.file_listbox.delete("0.0", "end")
                self.file_listbox.insert("end", f"Error: {str(e)}")
                self.status_label.configure(text="Failed to refresh files")
        
        threading.Thread(target=refresh, daemon=True).start()
    
    def download_file(self):
        """Download selected file"""
        if not self.file_list:
            messagebox.showinfo("Info", "No files available")
            return
        
        # File selection dialog
        dialog = ctk.CTkInputDialog(text="Enter file number to download:", title="Select File")
        selection = dialog.get_input()
        
        if not selection:
            return
        
        def download():
            try:
                file_index = int(selection) - 1
                if file_index < 0 or file_index >= len(self.file_list):
                    messagebox.showerror("Error", "Invalid file number")
                    return
                
                filename = self.file_list[file_index]
                
                # Ask where to save
                save_path = filedialog.asksaveasfilename(
                    initialfile=filename,
                    title="Save file as...",
                    defaultextension=".*"
                )
                
                if not save_path:
                    return
                
                self.status_label.configure(text="Downloading...")
                api.download_file(filename, save_path)
                
                messagebox.showinfo("Success", f"Downloaded '{filename}' successfully!")
                self.status_label.configure(text="Download completed")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
            except Exception as e:
                messagebox.showerror("Error", f"Download failed: {str(e)}")
                self.status_label.configure(text="Download failed")
        
        threading.Thread(target=download, daemon=True).start()
    
    def upload_file(self):
        """Upload file to server"""
        file_path = filedialog.askopenfilename(
            title="Select file to upload",
            filetypes=[("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        def upload():
            try:
                self.status_label.configure(text="Uploading...")
                api.upload_file(file_path)
                
                filename = os.path.basename(file_path)
                messagebox.showinfo("Success", f"Uploaded '{filename}' successfully!")
                self.status_label.configure(text="Upload completed")
                
                # Refresh file list
                self.refresh_files()
                
            except Exception as e:
                messagebox.showerror("Error", f"Upload failed: {str(e)}")
                self.status_label.configure(text="Upload failed")
        
        threading.Thread(target=upload, daemon=True).start()
    
    def on_closing(self):
        """Handle window closing"""
        if self.ngrok_manager.is_running:
            self.ngrok_manager.stop_ngrok()
        self.destroy()

if __name__ == "__main__":
    app = MainWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()