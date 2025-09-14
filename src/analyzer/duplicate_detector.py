import hashlib
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
from rich.console import Console
from rich.table import Table

from ..scanner.drive_scanner import DriveItem

@dataclass
class DuplicateGroup:
    files: List[DriveItem]
    detection_method: str
    confidence: float
    
    @property
    def total_size(self) -> int:
        return sum(f.size or 0 for f in self.files)
    
    @property
    def wasted_space(self) -> int:
        return self.total_size - (self.files[0].size or 0)

class DuplicateDetector:
    def __init__(self):
        self.console = Console()
    
    def find_duplicates(self, items: Dict[str, DriveItem]) -> List[DuplicateGroup]:
        files = [item for item in items.values() if not item.is_folder and item.size]
        duplicates = []
        
        self.console.print("🔍 Detecting duplicates...")
        
        # Method 1: Exact name and size match
        name_size_groups = self._group_by_name_and_size(files)
        for group in name_size_groups:
            if len(group) > 1:
                duplicates.append(DuplicateGroup(group, "Name + Size", 0.9))
        
        # Method 2: Same name, different case
        name_groups = self._group_by_similar_names(files)
        for group in name_groups:
            if len(group) > 1:
                duplicates.append(DuplicateGroup(group, "Similar Names", 0.7))
        
        # Method 3: Same size, similar names
        size_groups = self._group_by_size_and_similar_names(files)
        for group in size_groups:
            if len(group) > 1:
                duplicates.append(DuplicateGroup(group, "Size + Similar Name", 0.6))
        
        # Method 4: Exact size match (potential duplicates)
        size_only_groups = self._group_by_size_only(files)
        for group in size_only_groups:
            if len(group) > 1:
                duplicates.append(DuplicateGroup(group, "Same Size", 0.4))
        
        # Remove duplicates from results (files can appear in multiple groups)
        duplicates = self._deduplicate_groups(duplicates)
        
        self.console.print(f"✅ Found {len(duplicates)} duplicate groups")
        return duplicates
    
    def _group_by_name_and_size(self, files: List[DriveItem]) -> List[List[DriveItem]]:
        groups = defaultdict(list)
        for file in files:
            key = (file.name.lower(), file.size)
            groups[key].append(file)
        return [group for group in groups.values() if len(group) > 1]
    
    def _group_by_similar_names(self, files: List[DriveItem]) -> List[List[DriveItem]]:
        groups = defaultdict(list)
        for file in files:
            # Remove common suffixes and normalize
            name = self._normalize_filename(file.name)
            groups[name].append(file)
        return [group for group in groups.values() if len(group) > 1]
    
    def _group_by_size_and_similar_names(self, files: List[DriveItem]) -> List[List[DriveItem]]:
        groups = defaultdict(list)
        for file in files:
            name = self._normalize_filename(file.name)
            key = (name, file.size)
            groups[key].append(file)
        return [group for group in groups.values() if len(group) > 1]
    
    def _group_by_size_only(self, files: List[DriveItem]) -> List[List[DriveItem]]:
        groups = defaultdict(list)
        for file in files:
            if file.size and file.size > 1024 * 1024:  # Only files > 1MB
                groups[file.size].append(file)
        return [group for group in groups.values() if len(group) > 1]
    
    def _normalize_filename(self, filename: str) -> str:
        # Remove common duplicate indicators
        filename = filename.lower()
        suffixes_to_remove = [' (1)', ' (2)', ' (3)', ' (4)', ' (5)', 
                             ' copy', ' - copy', '_copy', ' duplicate']
        
        for suffix in suffixes_to_remove:
            filename = filename.replace(suffix, '')
        
        # Remove extra spaces
        filename = ' '.join(filename.split())
        return filename
    
    def _deduplicate_groups(self, groups: List[DuplicateGroup]) -> List[DuplicateGroup]:
        seen_files = set()
        unique_groups = []
        
        # Sort by confidence (highest first)
        groups.sort(key=lambda g: g.confidence, reverse=True)
        
        for group in groups:
            file_ids = {f.id for f in group.files}
            if not file_ids.intersection(seen_files):
                unique_groups.append(group)
                seen_files.update(file_ids)
        
        return unique_groups
    
    def print_duplicate_report(self, duplicates: List[DuplicateGroup]):
        if not duplicates:
            self.console.print("✅ No duplicates found!")
            return
        
        total_wasted = sum(group.wasted_space for group in duplicates)
        
        self.console.print(f"\n📊 Duplicate Analysis Report")
        self.console.print(f"Found {len(duplicates)} duplicate groups")
        self.console.print(f"Total wasted space: {self._format_size(total_wasted)}")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Group", style="dim", width=5)
        table.add_column("Method", style="cyan", width=12)
        table.add_column("Files", justify="right", style="green", width=6)
        table.add_column("Size Each", justify="right", width=10)
        table.add_column("Wasted", justify="right", style="red", width=10)
        table.add_column("File Paths", style="dim")
        
        for i, group in enumerate(duplicates, 1):
            # Show full paths instead of just names
            file_paths = []
            for f in group.files[:3]:  # Show up to 3 files
                # Use full path if available, otherwise just name
                path = f.path if f.path else f.name
                file_paths.append(path)
            
            if len(group.files) > 3:
                file_paths.append(f"... and {len(group.files) - 3} more")
            
            paths_text = "\n".join(file_paths)
            
            table.add_row(
                str(i),
                group.detection_method,
                str(len(group.files)),
                self._format_size(group.files[0].size or 0),
                self._format_size(group.wasted_space),
                paths_text
            )
        
        self.console.print(table)
    
    def _format_size(self, size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_idx = 0
        
        while size >= 1024 and unit_idx < len(units) - 1:
            size /= 1024
            unit_idx += 1
        
        return f"{size:.1f} {units[unit_idx]}"