import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.progress import Progress

from ..scanner.drive_scanner import DriveItem

@dataclass
class ReorganizationAction:
    action_type: str  # "move", "rename", "delete", "create_folder"
    source_item: Optional[DriveItem]
    target_location: str
    new_name: Optional[str] = None
    description: str = ""

class DriveOrganizer:
    def __init__(self, service):
        self.service = service
        self.console = Console()
        self.actions_queue: List[ReorganizationAction] = []
    
    def create_folder(self, name: str, parent_id: str = 'root') -> str:
        folder_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        
        try:
            folder = self.service.files().create(body=folder_metadata).execute()
            self.console.print(f"✅ Created folder: {name}")
            return folder['id']
        except Exception as e:
            self.console.print(f"❌ Failed to create folder {name}: {e}")
            return None
    
    def move_item(self, item_id: str, new_parent_id: str, current_parent_id: str = None) -> bool:
        try:
            if current_parent_id:
                # Remove from current parent and add to new parent
                file = self.service.files().update(
                    fileId=item_id,
                    addParents=new_parent_id,
                    removeParents=current_parent_id
                ).execute()
            else:
                # Just add to new parent
                file = self.service.files().update(
                    fileId=item_id,
                    addParents=new_parent_id
                ).execute()
            
            return True
        except Exception as e:
            self.console.print(f"❌ Failed to move item {item_id}: {e}")
            return False
    
    def rename_item(self, item_id: str, new_name: str) -> bool:
        try:
            self.service.files().update(
                fileId=item_id,
                body={'name': new_name}
            ).execute()
            return True
        except Exception as e:
            self.console.print(f"❌ Failed to rename item {item_id}: {e}")
            return False
    
    def delete_item(self, item_id: str) -> bool:
        try:
            self.service.files().delete(fileId=item_id).execute()
            return True
        except Exception as e:
            self.console.print(f"❌ Failed to delete item {item_id}: {e}")
            return False
    
    def organize_by_file_type(self, items: Dict[str, DriveItem], root_id: str = 'root', preview: bool = True) -> List[ReorganizationAction]:
        """Organize files by type into appropriate folders"""
        actions = []
        files = [item for item in items.values() if not item.is_folder]
        
        # Group files by type
        file_groups = {
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.tiff'],
            'Videos': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'],
            'Audio': ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg'],
            'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
            'Presentations': ['.ppt', '.pptx', '.odp'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz']
        }
        
        type_folders = {}
        
        for file in files:
            file_ext = self._get_file_extension(file.name)
            file_type = self._categorize_file(file.name, file_groups)
            
            if file_type:  # Process all files regardless of location
                # Create folder if needed
                if file_type not in type_folders:
                    actions.append(ReorganizationAction(
                        'create_folder',
                        None,
                        root_id,
                        file_type,
                        f"Create {file_type} folder"
                    ))
                    type_folders[file_type] = f"new_folder_{file_type}"
                
                # Move file
                actions.append(ReorganizationAction(
                    'move',
                    file,
                    type_folders[file_type],
                    None,
                    f"Move {file.name} to {file_type}"
                ))
        
        if preview:
            self._preview_actions(actions, "File Type Organization")
        
        return actions
    
    def organize_by_date(self, items: Dict[str, DriveItem], root_id: str = 'root', preview: bool = True) -> List[ReorganizationAction]:
        """Organize files by creation/modification date"""
        actions = []
        files = [item for item in items.values() if not item.is_folder]
        
        date_folders = {}
        
        for file in files:
            # Extract year from modified time (simplified)
            year = file.modified_time[:4] if file.modified_time else "Unknown"
            
            if year not in date_folders:
                actions.append(ReorganizationAction(
                    'create_folder',
                    None,
                    root_id,
                    year,
                    f"Create {year} folder"
                ))
                date_folders[year] = f"new_folder_{year}"
            
            actions.append(ReorganizationAction(
                'move',
                file,
                date_folders[year],
                None,
                f"Move {file.name} to {year}"
            ))
        
        if preview:
            self._preview_actions(actions, "Date-based Organization")
        
        return actions
    
    def clean_empty_folders(self, items: Dict[str, DriveItem], preview: bool = True) -> List[ReorganizationAction]:
        """Remove empty folders"""
        actions = []
        folders = [item for item in items.values() if item.is_folder]
        
        for folder in folders:
            # Check if folder is empty
            has_children = any(
                item.parents and folder.id in item.parents
                for item in items.values()
            )
            
            if not has_children:
                actions.append(ReorganizationAction(
                    'delete',
                    folder,
                    '',
                    None,
                    f"Delete empty folder: {folder.name}"
                ))
        
        if preview:
            self._preview_actions(actions, "Empty Folder Cleanup")
        
        return actions
    
    def fix_naming_issues(self, items: Dict[str, DriveItem], preview: bool = True) -> List[ReorganizationAction]:
        """Fix common naming issues"""
        actions = []
        
        for item in items.values():
            original_name = item.name
            fixed_name = self._fix_name(original_name)
            
            if fixed_name != original_name:
                actions.append(ReorganizationAction(
                    'rename',
                    item,
                    '',
                    fixed_name,
                    f"Rename '{original_name}' to '{fixed_name}'"
                ))
        
        if preview:
            self._preview_actions(actions, "Name Standardization")
        
        return actions
    
    def execute_actions(self, actions: List[ReorganizationAction], confirm: bool = True) -> bool:
        """Execute a list of reorganization actions"""
        if not actions:
            self.console.print("No actions to execute.")
            return True
        
        if confirm and not Confirm.ask(f"Execute {len(actions)} actions?"):
            self.console.print("Operation cancelled.")
            return False
        
        created_folders = {}
        success_count = 0
        
        with Progress() as progress:
            task = progress.add_task("Executing actions...", total=len(actions))
            
            for action in actions:
                success = False
                
                try:
                    if action.action_type == 'create_folder':
                        folder_id = self.create_folder(action.new_name, action.target_location)
                        if folder_id:
                            created_folders[f"new_folder_{action.new_name}"] = folder_id
                            success = True
                    
                    elif action.action_type == 'move':
                        target_id = created_folders.get(action.target_location, action.target_location)
                        current_parent = action.source_item.parents[0] if action.source_item.parents else None
                        success = self.move_item(action.source_item.id, target_id, current_parent)
                        if success:
                            self.console.print(f"📁 Moved: {action.source_item.name}")
                    
                    elif action.action_type == 'rename':
                        success = self.rename_item(action.source_item.id, action.new_name)
                        if success:
                            self.console.print(f"✏️ Renamed: {action.source_item.name}")
                    
                    elif action.action_type == 'delete':
                        success = self.delete_item(action.source_item.id)
                        if success:
                            self.console.print(f"🗑️ Deleted: {action.source_item.name}")
                    
                    if success:
                        success_count += 1
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    self.console.print(f"❌ Error executing action: {e}")
                
                progress.update(task, advance=1)
        
        self.console.print(f"\n✅ Completed {success_count}/{len(actions)} actions successfully")
        return success_count == len(actions)
    
    def _preview_actions(self, actions: List[ReorganizationAction], title: str):
        """Preview actions before execution"""
        self.console.print(f"\n🔍 Preview: {title}")
        
        if not actions:
            self.console.print("No actions needed.")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Action", style="cyan")
        table.add_column("Item", style="green")
        table.add_column("Details")
        
        for action in actions[:20]:  # Show first 20 actions
            item_name = action.source_item.name if action.source_item else "N/A"
            
            if action.action_type == 'create_folder':
                details = f"Create folder: {action.new_name}"
            elif action.action_type == 'move':
                details = f"Move to: {action.target_location}"
            elif action.action_type == 'rename':
                details = f"Rename to: {action.new_name}"
            elif action.action_type == 'delete':
                details = "Delete item"
            else:
                details = action.description
            
            table.add_row(action.action_type.title(), item_name, details)
        
        if len(actions) > 20:
            table.add_row("...", f"... and {len(actions) - 20} more actions", "...")
        
        self.console.print(table)
        self.console.print(f"Total actions: {len(actions)}")
    
    def _get_file_extension(self, filename: str) -> str:
        return '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    
    def _categorize_file(self, filename: str, file_groups: Dict[str, List[str]]) -> Optional[str]:
        ext = self._get_file_extension(filename)
        for category, extensions in file_groups.items():
            if ext in extensions:
                return category
        return None
    
    def _fix_name(self, name: str) -> str:
        """Fix common naming issues"""
        # Remove duplicate spaces
        fixed = ' '.join(name.split())
        
        # Remove leading/trailing spaces
        fixed = fixed.strip()
        
        # Replace problematic characters
        problematic = ['<', '>', ':', '"', '|', '?', '*']
        for char in problematic:
            fixed = fixed.replace(char, '_')
        
        return fixed