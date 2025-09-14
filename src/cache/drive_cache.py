import os
import json
import pickle
import time
from typing import Dict, Optional, List
from dataclasses import asdict
from pathlib import Path
from rich.console import Console

from ..scanner.drive_scanner import DriveItem

class DriveCache:
    def __init__(self, cache_dir: str = ".drive_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.console = Console()
        
        # Cache files
        self.metadata_file = self.cache_dir / "metadata.json"
        self.items_file = self.cache_dir / "items.pkl"
        
        # Default cache settings
        self.default_ttl_hours = 2  # Cache expires after 2 hours
    
    def save_scan_data(self, items: Dict[str, DriveItem], folder_id: str = 'root', ttl_hours: Optional[int] = None):
        """Save scanned Drive data to cache"""
        try:
            ttl = ttl_hours or self.default_ttl_hours
            
            # Save metadata
            metadata = {
                'folder_id': folder_id,
                'scan_time': time.time(),
                'ttl_seconds': ttl * 3600,
                'item_count': len(items),
                'expires_at': time.time() + (ttl * 3600)
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save items data (using pickle for complex objects)
            with open(self.items_file, 'wb') as f:
                pickle.dump(items, f)
            
            self.console.print(f"💾 Cached {len(items)} items (expires in {ttl}h)")
            
        except Exception as e:
            self.console.print(f"⚠️  Failed to save cache: {e}")
    
    def load_scan_data(self, folder_id: str = 'root', ignore_expiry: bool = False) -> Optional[Dict[str, DriveItem]]:
        """Load cached Drive data if available and valid"""
        try:
            # Check if cache files exist
            if not self.metadata_file.exists() or not self.items_file.exists():
                return None
            
            # Load metadata
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if cache is for the same folder
            if metadata.get('folder_id') != folder_id:
                return None
            
            # Check expiry (unless ignored)
            if not ignore_expiry:
                current_time = time.time()
                expires_at = metadata.get('expires_at', 0)
                
                if current_time > expires_at:
                    age_hours = (current_time - metadata.get('scan_time', 0)) / 3600
                    self.console.print(f"💨 Cache expired ({age_hours:.1f}h old)")
                    return None
            
            # Load items
            with open(self.items_file, 'rb') as f:
                items = pickle.load(f)
            
            age_minutes = (time.time() - metadata.get('scan_time', 0)) / 60
            self.console.print(f"📋 Using cached data ({age_minutes:.0f} minutes old, {len(items)} items)")
            return items
            
        except Exception as e:
            self.console.print(f"⚠️  Failed to load cache: {e}")
            return None
    
    def is_cache_valid(self, folder_id: str = 'root') -> bool:
        """Check if cache exists and is still valid"""
        try:
            if not self.metadata_file.exists():
                return False
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check folder match and expiry
            if metadata.get('folder_id') != folder_id:
                return False
            
            current_time = time.time()
            expires_at = metadata.get('expires_at', 0)
            
            return current_time <= expires_at
            
        except Exception:
            return False
    
    def get_cache_info(self) -> Optional[Dict]:
        """Get information about current cache"""
        try:
            if not self.metadata_file.exists():
                return None
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            current_time = time.time()
            scan_time = metadata.get('scan_time', 0)
            expires_at = metadata.get('expires_at', 0)
            
            age_hours = (current_time - scan_time) / 3600
            remaining_hours = max(0, (expires_at - current_time) / 3600)
            
            return {
                'folder_id': metadata.get('folder_id'),
                'item_count': metadata.get('item_count'),
                'age_hours': age_hours,
                'remaining_hours': remaining_hours,
                'is_expired': current_time > expires_at,
                'scan_time': time.ctime(scan_time),
                'expires_time': time.ctime(expires_at)
            }
            
        except Exception:
            return None
    
    def clear_cache(self):
        """Remove all cached data"""
        try:
            if self.metadata_file.exists():
                self.metadata_file.unlink()
            if self.items_file.exists():
                self.items_file.unlink()
            
            self.console.print("🗑️  Cache cleared")
            return True
            
        except Exception as e:
            self.console.print(f"❌ Failed to clear cache: {e}")
            return False
    
    def print_cache_status(self):
        """Print detailed cache status"""
        info = self.get_cache_info()
        
        if not info:
            self.console.print("📭 No cache available")
            return
        
        status_color = "red" if info['is_expired'] else "green"
        status_text = "EXPIRED" if info['is_expired'] else "VALID"
        
        self.console.print(f"\n💾 Cache Status: [{status_color}]{status_text}[/]")
        self.console.print(f"📁 Folder ID: {info['folder_id']}")
        self.console.print(f"📊 Items cached: {info['item_count']:,}")
        self.console.print(f"⏰ Age: {info['age_hours']:.1f} hours")
        
        if info['is_expired']:
            self.console.print(f"💨 Expired {-info['remaining_hours']:.1f} hours ago")
        else:
            self.console.print(f"⏳ Expires in: {info['remaining_hours']:.1f} hours")
        
        self.console.print(f"📅 Scanned: {info['scan_time']}")
        self.console.print(f"📅 Expires: {info['expires_time']}")

class CachedDriveScanner:
    """Wrapper around DriveScanner with caching capabilities"""
    
    def __init__(self, service, cache_ttl_hours: int = 2):
        self.scanner = None  # Will be imported dynamically to avoid circular imports
        self.service = service
        self.cache = DriveCache()
        self.cache_ttl_hours = cache_ttl_hours
    
    def scan_drive(self, folder_id: str = 'root', force_refresh: bool = False, use_cache: bool = True) -> Dict[str, DriveItem]:
        """Scan drive with caching support"""
        
        # Try to use cache first (unless force refresh)
        if use_cache and not force_refresh:
            cached_items = self.cache.load_scan_data(folder_id)
            if cached_items is not None:
                return cached_items
        
        # Import here to avoid circular imports
        if self.scanner is None:
            from ..scanner.drive_scanner import DriveScanner
            self.scanner = DriveScanner(self.service)
        
        # Perform fresh scan
        if force_refresh:
            self.cache.console.print("🔄 Force refresh requested - scanning fresh data...")
        else:
            self.cache.console.print("📡 No valid cache found - scanning fresh data...")
        
        items = self.scanner.scan_drive(folder_id)
        
        # Cache the results
        if use_cache:
            self.cache.save_scan_data(items, folder_id, self.cache_ttl_hours)
        
        return items
    
    def get_cache_status(self):
        """Get cache status"""
        return self.cache.get_cache_info()
    
    def clear_cache(self):
        """Clear cache"""
        return self.cache.clear_cache()
    
    def print_cache_status(self):
        """Print cache status"""
        self.cache.print_cache_status()