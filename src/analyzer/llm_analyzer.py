import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import ollama
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..scanner.drive_scanner import DriveItem

@dataclass
class SmartSuggestion:
    title: str
    description: str
    confidence: float
    actions: List[str]
    reasoning: str

@dataclass
class ProjectGroup:
    name: str
    folders: List[str]
    files: List[str]
    rationale: str

class LLMAnalyzer:
    def __init__(self, model: str = "gpt-oss:20b"):
        self.console = Console()
        self.model = model
        self._check_ollama_connection()
    
    def _check_ollama_connection(self):
        """Check if Ollama is running and the model is available"""
        try:
            # Test connection
            models = ollama.list()
            available_models = [model['name'] for model in models['models']]
            
            if not any(self.model in model for model in available_models):
                self.console.print(f"⚠️  Model {self.model} not found. Available models: {available_models}")
                self.console.print(f"💡 Run: ollama pull {self.model}")
                return False
            
            # Test a simple query
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': 'Hello! Just testing connection. Reply with "OK".'}
            ])
            
            if 'OK' in response['message']['content']:
                self.console.print(f"✅ Ollama connected successfully with model: {self.model}")
                return True
            
        except Exception as e:
            self.console.print(f"❌ Ollama connection failed: {e}")
            self.console.print("💡 Make sure Ollama is running: ollama serve")
            return False
    
    def analyze_folder_structure(self, items: Dict[str, DriveItem]) -> List[SmartSuggestion]:
        """Analyze folder structure and provide intelligent suggestions"""
        self.console.print("🧠 Analyzing folder structure with LLM...")
        
        # Prepare structure summary for LLM
        structure_summary = self._prepare_structure_summary(items)
        
        prompt = f"""
You are an expert at organizing digital file systems. Analyze this Google Drive structure and provide intelligent reorganization suggestions.

CURRENT STRUCTURE:
{structure_summary}

Please provide 3-5 actionable suggestions to improve this organization. Focus on:
1. Eliminating duplicate folders
2. Reducing excessive nesting (>5 levels)
3. Grouping related content logically
4. Using consistent naming conventions
5. Creating better project boundaries

Format your response as JSON with this structure:
{{
  "suggestions": [
    {{
      "title": "Brief title",
      "description": "Detailed description", 
      "confidence": 0.85,
      "actions": ["Action 1", "Action 2"],
      "reasoning": "Why this helps"
    }}
  ]
}}
"""
        
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            # Parse JSON response
            content = response['message']['content']
            
            # Extract JSON from response (might have extra text)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                data = json.loads(json_content)
                
                suggestions = []
                for item in data.get('suggestions', []):
                    suggestions.append(SmartSuggestion(
                        title=item['title'],
                        description=item['description'],
                        confidence=item['confidence'],
                        actions=item['actions'],
                        reasoning=item['reasoning']
                    ))
                
                return suggestions
            
        except Exception as e:
            self.console.print(f"❌ Error analyzing with LLM: {e}")
            return []
        
        return []
    
    def suggest_folder_name(self, folder_contents: List[DriveItem], current_name: str) -> str:
        """Suggest a better name for a folder based on its contents"""
        
        # Prepare content summary
        content_summary = self._prepare_content_summary(folder_contents)
        
        prompt = f"""
Suggest a better name for a folder currently called "{current_name}".

FOLDER CONTENTS:
{content_summary}

The new name should be:
- Descriptive and clear
- Consistent with good naming conventions
- Max 3-4 words
- Use hyphens or underscores instead of spaces

Reply with just the suggested folder name, nothing else.
"""
        
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            suggested_name = response['message']['content'].strip()
            # Clean up the suggestion
            suggested_name = suggested_name.replace('"', '').replace("'", "")
            return suggested_name if suggested_name else current_name
            
        except Exception as e:
            self.console.print(f"❌ Error getting folder name suggestion: {e}")
            return current_name
    
    def detect_project_boundaries(self, items: Dict[str, DriveItem]) -> List[ProjectGroup]:
        """Detect logical project groupings in the folder structure"""
        
        structure_summary = self._prepare_structure_summary(items)
        
        prompt = f"""
Analyze this Google Drive structure and identify logical project groups that should be organized together.

STRUCTURE:
{structure_summary}

Look for:
- Related folders that should be grouped together
- Academic/research projects
- Work projects
- Personal projects
- Travel/event folders
- Software/technical projects

Format your response as JSON:
{{
  "projects": [
    {{
      "name": "Project name",
      "folders": ["folder1", "folder2"],
      "files": ["file1.pdf"],
      "rationale": "Why these belong together"
    }}
  ]
}}
"""
        
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            content = response['message']['content']
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                data = json.loads(json_content)
                
                projects = []
                for item in data.get('projects', []):
                    projects.append(ProjectGroup(
                        name=item['name'],
                        folders=item.get('folders', []),
                        files=item.get('files', []),
                        rationale=item['rationale']
                    ))
                
                return projects
            
        except Exception as e:
            self.console.print(f"❌ Error detecting project boundaries: {e}")
            return []
        
        return []
    
    def _prepare_structure_summary(self, items: Dict[str, DriveItem], max_items: int = 100) -> str:
        """Prepare a concise summary of folder structure for LLM"""
        folders = [item for item in items.values() if item.is_folder]
        files = [item for item in items.values() if not item.is_folder]
        
        # Sort by path depth to show structure
        folders.sort(key=lambda x: (x.path.count('/'), x.path))
        
        summary = []
        summary.append(f"TOTAL: {len(folders)} folders, {len(files)} files\n")
        
        # Show folder hierarchy (limited)
        summary.append("FOLDER STRUCTURE:")
        for folder in folders[:max_items]:
            depth = folder.path.count('/')
            indent = "  " * depth
            child_count = len([f for f in items.values() if f.parents and folder.id in f.parents])
            summary.append(f"{indent}- {folder.name}/ ({child_count} items)")
        
        if len(folders) > max_items:
            summary.append(f"... and {len(folders) - max_items} more folders")
        
        # Show some file types
        file_extensions = {}
        for file in files:
            ext = file.name.split('.')[-1].lower() if '.' in file.name else 'no-ext'
            file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        summary.append(f"\nFILE TYPES: {dict(list(file_extensions.items())[:20])}")
        
        return "\n".join(summary)
    
    def _prepare_content_summary(self, contents: List[DriveItem]) -> str:
        """Prepare a summary of folder contents"""
        if not contents:
            return "Empty folder"
        
        folders = [item for item in contents if item.is_folder]
        files = [item for item in contents if not item.is_folder]
        
        summary = []
        summary.append(f"{len(folders)} folders, {len(files)} files")
        
        if folders:
            folder_names = [f.name for f in folders[:10]]
            summary.append(f"Folders: {', '.join(folder_names)}")
            if len(folders) > 10:
                summary.append(f"... and {len(folders) - 10} more folders")
        
        if files:
            # Show file types
            extensions = {}
            for file in files:
                ext = file.name.split('.')[-1].lower() if '.' in file.name else 'no-ext'
                extensions[ext] = extensions.get(ext, 0) + 1
            
            summary.append(f"File types: {dict(list(extensions.items())[:10])}")
            
            # Show some file names
            file_names = [f.name for f in files[:5]]
            summary.append(f"Sample files: {', '.join(file_names)}")
        
        return "\n".join(summary)
    
    def print_smart_suggestions(self, suggestions: List[SmartSuggestion]):
        """Print LLM suggestions in a nice format"""
        if not suggestions:
            self.console.print("🤔 No LLM suggestions generated")
            return
        
        self.console.print("\n🧠 AI-Powered Reorganization Suggestions")
        
        for i, suggestion in enumerate(suggestions, 1):
            # Create confidence indicator
            confidence_color = "green" if suggestion.confidence > 0.8 else "yellow" if suggestion.confidence > 0.6 else "red"
            confidence_bar = "█" * int(suggestion.confidence * 10)
            
            panel_content = f"""[bold]{suggestion.description}[/]

[yellow]Confidence:[/] [{confidence_color}]{confidence_bar}[/] {suggestion.confidence:.1%}

[cyan]Actions:[/]
{chr(10).join(f"  • {action}" for action in suggestion.actions)}

[dim]Reasoning: {suggestion.reasoning}[/]"""
            
            self.console.print(Panel(
                panel_content,
                title=f"💡 {i}. {suggestion.title}",
                border_style="blue"
            ))