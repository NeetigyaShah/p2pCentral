import requests
import json
import os

class ServerConfig:
    def __init__(self):
        self.config_file = "server_config.json"
        self.default_local = "http://localhost:5000"
        self.current_url = self.load_config()
    
    def load_config(self):
        """Load server URL from config file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('server_url', self.default_local)
            except:
                pass
        return self.default_local
    
    def save_config(self, url):
        """Save server URL to config file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'server_url': url}, f)
            self.current_url = url
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def get_url(self):
        return self.current_url
    
    def set_url(self, url):
        # Clean up URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        if url.endswith('/'):
            url = url[:-1]
        self.save_config(url)

# Global server config
server_config = ServerConfig()

def test_connection(url=None):
    """Test if server is reachable"""
    test_url = url or server_config.get_url()
    try:
        response = requests.get(f"{test_url}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def list_files():
    """Get list of files from server"""
    r = requests.get(f"{server_config.get_url()}/files", timeout=10)
    r.raise_for_status()
    return r.json()

def download_file(filename, dest_path):
    """Download file from server"""
    r = requests.get(f"{server_config.get_url()}/download/{filename}", 
                    stream=True, timeout=30)
    r.raise_for_status()
    
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def upload_file(filepath):
    """Upload file to server"""
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        files = {"file": (filename, f)}
        r = requests.post(f"{server_config.get_url()}/upload", 
                         files=files, timeout=60)
        r.raise_for_status()

def get_server_url():
    """Get current server URL"""
    return server_config.get_url()

def set_server_url(url):
    """Set new server URL"""
    server_config.set_url(url)