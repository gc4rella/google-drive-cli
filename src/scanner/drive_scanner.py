import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, TaskID

@dataclass
class DriveItem:
    id: str
    name: str
    mime_type: str
    size: Optional[int]
    parents: List[str]
    created_time: str
    modified_time: str
    path: str = ""
    is_folder: bool = False
    
    def __post_init__(self):
        self.is_folder = self.mime_type == 'application/vnd.google-apps.folder'

class DriveScanner:
    def __init__(self, service):
        self.service = service
        self.console = Console()
        self.items: Dict[str, DriveItem] = {}
        self.folder_structure: Dict[str, List[str]] = {}
    
    def scan_drive(self, root_folder_id: str = 'root') -> Dict[str, DriveItem]:
        self.console.print("🔍 Starting Google Drive scan...")
        
        with Progress() as progress:
            task = progress.add_task("Scanning files...", total=None)
            self._scan_recursive(root_folder_id, "", progress, task)
        
        self._build_paths()
        self.console.print(f"✅ Scan complete! Found {len(self.items)} items")
        return self.items
    
    def _scan_recursive(self, folder_id: str, current_path: str, progress: Progress, task: TaskID):
        page_token = None
        
        while True:
            try:
                results = self.service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="nextPageToken, files(id, name, mimeType, size, parents, createdTime, modifiedTime)",
                    pageSize=1000,
                    pageToken=page_token
                ).execute()
                
                items = results.get('files', [])
                
                for item in items:
                    drive_item = DriveItem(
                        id=item['id'],
                        name=item['name'],
                        mime_type=item['mimeType'],
                        size=int(item.get('size', 0)) if item.get('size') else None,
                        parents=item.get('parents', []),
                        created_time=item['createdTime'],
                        modified_time=item['modifiedTime']
                    )
                    
                    self.items[item['id']] = drive_item
                    
                    if drive_item.is_folder:
                        self.folder_structure[item['id']] = []
                        folder_path = f"{current_path}/{item['name']}" if current_path else item['name']
                        progress.update(task, description=f"Scanning: {folder_path}")
                        self._scan_recursive(item['id'], folder_path, progress, task)
                    
                    if folder_id in self.folder_structure:
                        self.folder_structure[folder_id].append(item['id'])
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            except Exception as e:
                self.console.print(f"❌ Error scanning folder {folder_id}: {e}")
                break
    
    def _build_paths(self):
        def get_path(item_id: str, visited: set = None) -> str:
            if visited is None:
                visited = set()
            
            if item_id in visited:
                return "[CIRCULAR]"
            
            if item_id == 'root':
                return ""
            
            item = self.items.get(item_id)
            if not item or not item.parents:
                return item.name if item else "[UNKNOWN]"
            
            visited.add(item_id)
            parent_path = get_path(item.parents[0], visited)
            visited.remove(item_id)
            
            if parent_path:
                return f"{parent_path}/{item.name}"
            else:
                return item.name
        
        for item_id, item in self.items.items():
            item.path = get_path(item_id)
    
    def get_folder_items(self, folder_id: str) -> List[DriveItem]:
        return [self.items[item_id] for item_id in self.folder_structure.get(folder_id, [])]
    
    def get_all_folders(self) -> List[DriveItem]:
        return [item for item in self.items.values() if item.is_folder]
    
    def get_all_files(self) -> List[DriveItem]:
        return [item for item in self.items.values() if not item.is_folder]
    
    def find_items_by_name(self, name: str, case_sensitive: bool = False) -> List[DriveItem]:
        if case_sensitive:
            return [item for item in self.items.values() if name in item.name]
        else:
            name_lower = name.lower()
            return [item for item in self.items.values() if name_lower in item.name.lower()]
    
    def get_folder_depth(self, item_id: str) -> int:
        return item.path.count('/') if (item := self.items.get(item_id)) else 0