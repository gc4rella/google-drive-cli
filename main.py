#!/usr/bin/env python3
"""
Google Drive CLI Manager
A command-line tool to analyze, organize, and restructure your Google Drive folders efficiently.
"""

import click
from rich.console import Console
from rich.panel import Panel

from src.auth.google_auth import GoogleDriveAuth
from src.scanner.drive_scanner import DriveScanner
from src.cache.drive_cache import CachedDriveScanner
from src.analyzer.duplicate_detector import DuplicateDetector
from src.analyzer.structure_analyzer import StructureAnalyzer
from src.analyzer.llm_analyzer import LLMAnalyzer
from src.reorganizer.drive_organizer import DriveOrganizer

console = Console()

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Google Drive CLI Manager - Organize your Drive efficiently"""
    console.print(Panel.fit(
        "[bold blue]Google Drive CLI Manager[/]\n"
        "Analyze, organize, and restructure your Google Drive",
        style="blue"
    ))

@cli.command()
@click.option('--folder-id', default='root', help='Folder ID to scan (default: root)')
@click.option('--force-refresh', is_flag=True, help='Force fresh scan, ignore cache')
@click.option('--no-cache', is_flag=True, help='Disable caching for this scan')
@click.option('--cache-ttl', default=2, help='Cache time-to-live in hours (default: 2)')
def scan(folder_id, force_refresh, no_cache, cache_ttl):
    """Scan and analyze your Google Drive structure"""
    try:
        # Initialize components
        auth = GoogleDriveAuth()
        scanner = CachedDriveScanner(auth.get_service(), cache_ttl_hours=cache_ttl)
        analyzer = StructureAnalyzer()
        
        # Test connection
        if not auth.test_connection():
            console.print("❌ Failed to connect to Google Drive")
            return
        
        # Scan drive with caching
        use_cache = not no_cache
        items = scanner.scan_drive(folder_id, force_refresh=force_refresh, use_cache=use_cache)
        
        # Analyze structure
        issues, suggestions = analyzer.analyze_structure(items)
        analyzer.print_analysis_report(issues, suggestions)
        analyzer.visualize_structure(items)
        
    except FileNotFoundError as e:
        console.print(f"❌ {e}")
        console.print("Please download credentials.json from Google Cloud Console")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
@click.option('--folder-id', default='root', help='Folder ID to scan (default: root)')
@click.option('--force-refresh', is_flag=True, help='Force fresh scan, ignore cache')
@click.option('--no-cache', is_flag=True, help='Disable caching for this scan')
def duplicates(folder_id, force_refresh, no_cache):
    """Find and report duplicate files"""
    try:
        # Initialize components
        auth = GoogleDriveAuth()
        scanner = CachedDriveScanner(auth.get_service())
        detector = DuplicateDetector()
        
        # Scan with caching
        use_cache = not no_cache
        items = scanner.scan_drive(folder_id, force_refresh=force_refresh, use_cache=use_cache)
        
        # Find duplicates
        duplicate_groups = detector.find_duplicates(items)
        detector.print_duplicate_report(duplicate_groups)
        
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
@click.option('--folder-id', default='root', help='Folder ID to scan (default: root)')
@click.option('--method', type=click.Choice(['type', 'date', 'custom']), default='type',
              help='Organization method (default: type)')
@click.option('--preview/--no-preview', default=True, help='Preview changes before applying')
@click.option('--execute/--no-execute', default=False, help='Execute the reorganization')
def organize(folder_id, method, preview, execute):
    """Reorganize your Google Drive"""
    try:
        # Initialize components
        auth = GoogleDriveAuth()
        scanner = DriveScanner(auth.get_service())
        organizer = DriveOrganizer(auth.get_service())
        
        # Scan drive
        items = scanner.scan_drive(folder_id)
        
        # Generate reorganization plan
        actions = []
        if method == 'type':
            actions = organizer.organize_by_file_type(items, folder_id, preview)
        elif method == 'date':
            actions = organizer.organize_by_date(items, folder_id, preview)
        
        if execute and actions:
            organizer.execute_actions(actions, confirm=True)
        elif not execute:
            console.print("\nTo execute these changes, run with --execute flag")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
@click.option('--folder-id', default='root', help='Folder ID to scan (default: root)')
@click.option('--execute/--no-execute', default=False, help='Execute the cleanup')
def cleanup(folder_id, execute):
    """Clean up empty folders and fix naming issues"""
    try:
        # Initialize components
        auth = GoogleDriveAuth()
        scanner = DriveScanner(auth.get_service())
        organizer = DriveOrganizer(auth.get_service())
        
        # Scan drive
        items = scanner.scan_drive(folder_id)
        
        # Generate cleanup actions
        empty_folder_actions = organizer.clean_empty_folders(items, preview=True)
        naming_actions = organizer.fix_naming_issues(items, preview=True)
        
        all_actions = empty_folder_actions + naming_actions
        
        if execute and all_actions:
            organizer.execute_actions(all_actions, confirm=True)
        elif not execute:
            console.print("\nTo execute these changes, run with --execute flag")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
def setup():
    """Setup Google Drive API credentials"""
    console.print(Panel(
        "[bold]Setup Instructions[/]\n\n"
        "1. Go to [link]https://console.cloud.google.com[/]\n"
        "2. Create a new project or select existing\n"
        "3. Enable Google Drive API\n"
        "4. Create OAuth 2.0 credentials (Desktop app)\n"
        "5. Download and save as 'credentials.json'\n"
        "6. Run any command to authenticate",
        title="Google Drive API Setup"
    ))

@cli.command()
@click.option('--folder-id', default='root', help='Folder ID to analyze (default: root)')
@click.option('--model', default='gpt-oss:20b', help='Ollama model to use (default: gpt-oss:20b)')
@click.option('--force-refresh', is_flag=True, help='Force fresh scan, ignore cache')
@click.option('--no-cache', is_flag=True, help='Disable caching for this scan')
def smart_analyze(folder_id, model, force_refresh, no_cache):
    """AI-powered intelligent folder structure analysis"""
    try:
        # Initialize components
        auth = GoogleDriveAuth()
        scanner = CachedDriveScanner(auth.get_service())
        llm_analyzer = LLMAnalyzer(model=model)
        
        # Scan drive with caching
        use_cache = not no_cache
        items = scanner.scan_drive(folder_id, force_refresh=force_refresh, use_cache=use_cache)
        
        # Get AI suggestions
        suggestions = llm_analyzer.analyze_folder_structure(items)
        llm_analyzer.print_smart_suggestions(suggestions)
        
        # Detect project boundaries
        console.print("\n🎯 Detecting Project Boundaries...")
        projects = llm_analyzer.detect_project_boundaries(items)
        
        if projects:
            console.print(f"\n📂 Found {len(projects)} potential project groups:")
            for project in projects:
                console.print(f"• [bold cyan]{project.name}[/]: {len(project.folders)} folders, {len(project.files)} files")
                console.print(f"  [dim]{project.rationale}[/]")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
@click.option('--folder-id', default='root', help='Folder ID to analyze (default: root)')
@click.option('--model', default='gpt-oss:20b', help='Ollama model to use')
@click.option('--execute/--no-execute', default=False, help='Execute the LLM suggestions')
def smart_organize(folder_id, model, execute):
    """AI-powered folder reorganization"""
    try:
        # Initialize components
        auth = GoogleDriveAuth()
        scanner = DriveScanner(auth.get_service())
        llm_analyzer = LLMAnalyzer(model=model)
        organizer = DriveOrganizer(auth.get_service())
        
        # Scan drive
        items = scanner.scan_drive(folder_id)
        
        # Get AI suggestions
        suggestions = llm_analyzer.analyze_folder_structure(items)
        llm_analyzer.print_smart_suggestions(suggestions)
        
        if execute:
            console.print("\n⚠️  LLM-based execution not yet implemented")
            console.print("💡 Use regular organize commands for now, guided by AI suggestions above")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
@click.argument('folder_name')
@click.option('--folder-id', help='Specific folder ID to rename')
@click.option('--model', default='gpt-oss:20b', help='Ollama model to use')
def smart_rename(folder_name, folder_id, model):
    """Get AI suggestions for better folder names"""
    try:
        # Initialize components
        auth = GoogleDriveAuth()
        scanner = DriveScanner(auth.get_service())
        llm_analyzer = LLMAnalyzer(model=model)
        
        if folder_id:
            # Analyze specific folder
            items = scanner.scan_drive('root')  # Need full scan to get context
            folder_items = [item for item in items.values() if item.parents and folder_id in item.parents]
            
            if folder_items:
                suggestion = llm_analyzer.suggest_folder_name(folder_items, folder_name)
                console.print(f"💡 Suggested name for '{folder_name}': [bold green]{suggestion}[/]")
            else:
                console.print("❌ Folder not found or empty")
        else:
            console.print("❌ Please provide --folder-id")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
def cache_status():
    """Show cache status and information"""
    try:
        from src.cache.drive_cache import DriveCache
        cache = DriveCache()
        cache.print_cache_status()
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear the cache?')
def cache_clear():
    """Clear all cached data"""
    try:
        from src.cache.drive_cache import DriveCache
        cache = DriveCache()
        cache.clear_cache()
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
@click.option('--ttl', default=2, help='Cache time-to-live in hours (default: 2)')
@click.option('--folder-id', default='root', help='Folder ID to cache (default: root)')
def cache_refresh(ttl, folder_id):
    """Force refresh cache with new data"""
    try:
        auth = GoogleDriveAuth()
        scanner = CachedDriveScanner(auth.get_service(), cache_ttl_hours=ttl)
        
        # Force refresh and cache
        console.print(f"🔄 Refreshing cache (TTL: {ttl}h)...")
        items = scanner.scan_drive(folder_id, force_refresh=True, use_cache=True)
        console.print(f"✅ Cache refreshed with {len(items)} items")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")

@cli.command()
def test():
    """Test Google Drive connection"""
    try:
        auth = GoogleDriveAuth()
        if auth.test_connection():
            console.print("✅ Google Drive connection successful!")
            
            # Get basic info
            service = auth.get_service()
            about = service.about().get(fields="user,storageQuota").execute()
            
            user = about.get('user', {})
            storage = about.get('storageQuota', {})
            
            console.print(f"📧 Account: {user.get('emailAddress', 'Unknown')}")
            console.print(f"👤 Name: {user.get('displayName', 'Unknown')}")
            
            if storage:
                used = int(storage.get('usage', 0))
                limit = int(storage.get('limit', 0))
                
                if limit > 0:
                    usage_percent = (used / limit) * 100
                    console.print(f"💾 Storage: {used // (1024**3):.1f}GB / {limit // (1024**3):.1f}GB ({usage_percent:.1f}%)")
        else:
            console.print("❌ Connection failed")
    except Exception as e:
        console.print(f"❌ Error: {e}")

if __name__ == '__main__':
    cli()