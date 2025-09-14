from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
import re
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from ..scanner.drive_scanner import DriveItem

@dataclass
class StructureIssue:
    issue_type: str
    description: str
    items: List[DriveItem]
    severity: str  # "low", "medium", "high"
    suggestion: str

@dataclass
class ReorganizationSuggestion:
    title: str
    description: str
    actions: List[str]
    estimated_improvement: str

class StructureAnalyzer:
    def __init__(self):
        self.console = Console()
    
    def analyze_structure(self, items: Dict[str, DriveItem]) -> Tuple[List[StructureIssue], List[ReorganizationSuggestion]]:
        self.console.print("📊 Analyzing folder structure...")
        
        issues = []
        suggestions = []
        
        # Get all folders and files
        folders = [item for item in items.values() if item.is_folder]
        files = [item for item in items.values() if not item.is_folder]
        
        # Analysis 1: Deep nesting
        deep_folders = self._find_deeply_nested_folders(folders)
        if deep_folders:
            issues.append(StructureIssue(
                "Deep Nesting",
                f"Found {len(deep_folders)} folders nested more than 5 levels deep",
                deep_folders,
                "medium",
                "Consider flattening the hierarchy or using more descriptive folder names"
            ))
        
        # Analysis 2: Empty folders
        empty_folders = self._find_empty_folders(items, folders)
        if empty_folders:
            issues.append(StructureIssue(
                "Empty Folders",
                f"Found {len(empty_folders)} empty folders taking up space",
                empty_folders,
                "low",
                "Consider removing empty folders or consolidating with similar folders"
            ))
        
        # Analysis 3: Files in root
        root_files = self._find_root_files(files)
        if root_files:
            issues.append(StructureIssue(
                "Root Clutter",
                f"Found {len(root_files)} files in the root directory",
                root_files,
                "high",
                "Organize root files into appropriate folders"
            ))
        
        # Analysis 4: Naming inconsistencies
        naming_issues = self._analyze_naming_patterns(folders)
        if naming_issues:
            issues.append(naming_issues)
        
        # Analysis 5: File type scatter
        scattered_types = self._find_scattered_file_types(files)
        if scattered_types:
            for file_type, scattered_files in scattered_types.items():
                issues.append(StructureIssue(
                    "Scattered File Types",
                    f"{file_type} files are scattered across {len(set(f.path.split('/')[0] for f in scattered_files))} different folders",
                    scattered_files,
                    "medium",
                    f"Consider creating a dedicated folder for {file_type} files"
                ))
        
        # Generate suggestions
        suggestions = self._generate_suggestions(issues, folders, files)
        
        self.console.print(f"✅ Analysis complete! Found {len(issues)} issues")
        return issues, suggestions
    
    def _find_deeply_nested_folders(self, folders: List[DriveItem]) -> List[DriveItem]:
        return [folder for folder in folders if folder.path.count('/') > 5]
    
    def _find_empty_folders(self, all_items: Dict[str, DriveItem], folders: List[DriveItem]) -> List[DriveItem]:
        empty = []
        for folder in folders:
            has_children = any(
                item.parents and folder.id in item.parents 
                for item in all_items.values()
            )
            if not has_children:
                empty.append(folder)
        return empty
    
    def _find_root_files(self, files: List[DriveItem]) -> List[DriveItem]:
        return [file for file in files if '/' not in file.path]
    
    def _analyze_naming_patterns(self, folders: List[DriveItem]) -> StructureIssue:
        inconsistent_folders = []
        
        # Check for common naming issues
        patterns = {
            'mixed_case': re.compile(r'[a-z]+[A-Z]+|[A-Z]+[a-z]+'),
            'special_chars': re.compile(r'[!@#$%^&*()+=\[\]{}|;:,.<>?]'),
            'multiple_spaces': re.compile(r'\s{2,}'),
            'leading_trailing_space': re.compile(r'^\s+|\s+$')
        }
        
        issues_found = defaultdict(list)
        
        for folder in folders:
            name = folder.name
            for pattern_name, pattern in patterns.items():
                if pattern.search(name):
                    issues_found[pattern_name].append(folder)
        
        if issues_found:
            all_inconsistent = []
            for pattern_folders in issues_found.values():
                all_inconsistent.extend(pattern_folders)
            
            return StructureIssue(
                "Naming Inconsistencies",
                f"Found folders with inconsistent naming patterns",
                all_inconsistent,
                "low",
                "Standardize folder naming (e.g., use consistent case, avoid special characters)"
            )
        
        return None
    
    def _find_scattered_file_types(self, files: List[DriveItem]) -> Dict[str, List[DriveItem]]:
        type_locations = defaultdict(lambda: defaultdict(list))
        
        # Group files by type and location
        for file in files:
            file_ext = self._get_file_extension(file.name)
            folder_path = '/'.join(file.path.split('/')[:-1]) if '/' in file.path else 'root'
            type_locations[file_ext][folder_path].append(file)
        
        # Find types that are scattered across multiple locations
        scattered = {}
        for file_type, locations in type_locations.items():
            if len(locations) > 3 and sum(len(files) for files in locations.values()) > 5:
                all_files = []
                for files in locations.values():
                    all_files.extend(files)
                scattered[file_type] = all_files
        
        return scattered
    
    def _get_file_extension(self, filename: str) -> str:
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            # Group similar extensions
            doc_types = {'doc', 'docx', 'pdf', 'txt', 'rtf'}
            image_types = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'}
            video_types = {'mp4', 'avi', 'mov', 'mkv', 'flv'}
            audio_types = {'mp3', 'wav', 'flac', 'aac', 'm4a'}
            
            if ext in doc_types:
                return 'Documents'
            elif ext in image_types:
                return 'Images'
            elif ext in video_types:
                return 'Videos'
            elif ext in audio_types:
                return 'Audio'
            else:
                return ext.upper()
        return 'No Extension'
    
    def _generate_suggestions(self, issues: List[StructureIssue], folders: List[DriveItem], files: List[DriveItem]) -> List[ReorganizationSuggestion]:
        suggestions = []
        
        # Suggestion 1: Create organized structure
        if any(issue.issue_type == "Root Clutter" for issue in issues):
            suggestions.append(ReorganizationSuggestion(
                "Organize Root Directory",
                "Create a clean folder structure in your root directory",
                [
                    "Create main categories: Documents, Images, Videos, Projects",
                    "Move files from root into appropriate category folders",
                    "Create date-based subfolders for better organization"
                ],
                "Significantly improved navigation and reduced clutter"
            ))
        
        # Suggestion 2: Consolidate file types
        if any(issue.issue_type == "Scattered File Types" for issue in issues):
            suggestions.append(ReorganizationSuggestion(
                "Consolidate File Types",
                "Group similar files together by type or project",
                [
                    "Create dedicated folders for each file type (Images, Documents, etc.)",
                    "Move scattered files of the same type together",
                    "Consider project-based organization for work files"
                ],
                "Easier file discovery and better organization"
            ))
        
        # Suggestion 3: Flatten deep hierarchies
        if any(issue.issue_type == "Deep Nesting" for issue in issues):
            suggestions.append(ReorganizationSuggestion(
                "Flatten Deep Hierarchies",
                "Reduce excessive folder nesting for better navigation",
                [
                    "Identify folders nested more than 4-5 levels deep",
                    "Combine intermediate folders with descriptive names",
                    "Move frequently accessed files closer to the root"
                ],
                "Faster navigation and reduced complexity"
            ))
        
        # Suggestion 4: Archive old content
        old_files = [f for f in files if self._is_old_file(f)]
        if len(old_files) > 50:
            suggestions.append(ReorganizationSuggestion(
                "Archive Old Content",
                f"Archive {len(old_files)} files that haven't been modified in over a year",
                [
                    "Create an 'Archive' folder in root",
                    "Move files older than 1 year to archive",
                    "Organize archive by year or project"
                ],
                "Reduced clutter and improved performance"
            ))
        
        return suggestions
    
    def _is_old_file(self, file: DriveItem) -> bool:
        # Simple heuristic - check if file is older than 1 year
        # In a real implementation, you'd parse the date properly
        return '2022' in file.modified_time or '2021' in file.modified_time
    
    def print_analysis_report(self, issues: List[StructureIssue], suggestions: List[ReorganizationSuggestion]):
        self.console.print("\n📊 Structure Analysis Report")
        
        if not issues:
            self.console.print("✅ Your Drive structure looks good!")
            return
        
        # Issues table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Issue", style="cyan")
        table.add_column("Severity", justify="center")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Description")
        
        for issue in issues:
            severity_color = {"low": "green", "medium": "yellow", "high": "red"}
            table.add_row(
                issue.issue_type,
                f"[{severity_color[issue.severity]}]{issue.severity.upper()}[/]",
                str(len(issue.items)),
                issue.description
            )
        
        self.console.print(table)
        
        # Suggestions
        if suggestions:
            self.console.print("\n💡 Reorganization Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"\n[bold cyan]{i}. {suggestion.title}[/]")
                self.console.print(f"   {suggestion.description}")
                self.console.print(f"   [green]Expected improvement:[/] {suggestion.estimated_improvement}")
    
    def visualize_structure(self, items: Dict[str, DriveItem], max_depth: int = 3):
        self.console.print("\n🌳 Folder Structure Visualization")
        
        # Build tree structure
        tree = Tree("📁 My Drive")
        folder_nodes = {"root": tree}
        
        # Sort folders by depth to ensure parents are created first
        folders = [item for item in items.values() if item.is_folder]
        folders.sort(key=lambda x: x.path.count('/'))
        
        for folder in folders:
            if folder.path.count('/') > max_depth:
                continue
                
            parent_path = '/'.join(folder.path.split('/')[:-1]) if '/' in folder.path else 'root'
            parent_node = folder_nodes.get(parent_path, tree)
            
            # Count children
            children_count = sum(1 for item in items.values() 
                               if item.parents and folder.id in item.parents)
            
            folder_node = parent_node.add(f"📁 {folder.name} ({children_count} items)")
            folder_nodes[folder.path] = folder_node
        
        self.console.print(tree)