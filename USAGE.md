# Google Drive CLI Manager - Usage Guide

## Quick Start

### Option 1: Automated Setup (Recommended)

**For macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**For Windows:**
```batch
setup.bat
```

### Option 2: Manual Setup

1. **Create virtual environment:**
   ```bash
   # Create virtual environment
   python -m venv drive-cli-env
   
   # Activate it
   # macOS/Linux:
   source drive-cli-env/bin/activate
   # Windows:
   drive-cli-env\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Drive API:**
   ```bash
   python main.py setup
   ```
   Follow the instructions to download `credentials.json`

3. **Test connection:**
   ```bash
   python main.py test
   ```

## Commands

### `scan` - Analyze Drive Structure
```bash
# Scan entire Drive
python main.py scan

# Scan specific folder
python main.py scan --folder-id "your-folder-id"
```

**What it does:**
- Scans your entire Google Drive recursively
- Identifies structural issues (deep nesting, root clutter, naming problems)
- Provides reorganization suggestions
- Shows folder hierarchy visualization

### `duplicates` - Find Duplicate Files
```bash
python main.py duplicates
```

**Detection methods:**
- Exact name and size matches (90% confidence)
- Similar names with variations (70% confidence)  
- Same size with similar names (60% confidence)
- Files with identical sizes (40% confidence)

### `organize` - Reorganize Files
```bash
# Organize by file type (default)
python main.py organize --preview

# Organize by date
python main.py organize --method date --preview

# Execute the reorganization
python main.py organize --method type --execute
```

**Organization methods:**
- **type**: Groups files into Documents, Images, Videos, etc.
- **date**: Organizes files by creation/modification year

### `cleanup` - Clean Up Drive
```bash
# Preview cleanup actions
python main.py cleanup

# Execute cleanup
python main.py cleanup --execute
```

**What it cleans:**
- Empty folders
- Naming inconsistencies (spaces, special characters)
- Standardizes folder names

## Examples

### Example 1: Complete Drive Analysis
```bash
# First, scan and analyze your drive
python main.py scan

# Find duplicates to free up space
python main.py duplicates

# Preview organization by file type
python main.py organize --method type --preview

# Execute if you're happy with the preview
python main.py organize --method type --execute
```

### Example 2: Targeted Folder Organization
```bash
# Get folder ID from Drive URL or scan results
python main.py scan --folder-id "your-folder-id"

# Organize just that folder
python main.py organize --folder-id "your-folder-id" --execute
```

### Example 3: Maintenance Cleanup
```bash
# Regular cleanup of empty folders and naming
python main.py cleanup --execute
```

## Understanding the Output

### Structure Analysis Report
- **Deep Nesting**: Folders nested more than 5 levels deep
- **Root Clutter**: Files scattered in root directory
- **Scattered File Types**: Similar files spread across folders
- **Naming Inconsistencies**: Non-standard folder names

### Duplicate Detection Report
- **Confidence levels**: How likely files are to be duplicates
- **Wasted space**: Storage consumed by duplicate files
- **Detection method**: How duplicates were identified

### Reorganization Preview
- **Actions**: What will be moved/renamed/created
- **Impact**: Expected improvements to organization

## Safety Features

- **Preview mode**: See all changes before applying them
- **Confirmation prompts**: Explicit confirmation for destructive actions
- **Rate limiting**: Respects Google API limits
- **Error handling**: Graceful failure with detailed error messages

## Tips for Best Results

1. **Start with scanning**: Always run `scan` first to understand your Drive structure
2. **Use preview mode**: Always preview reorganization before executing
3. **Handle duplicates first**: Remove duplicates before reorganizing
4. **Work incrementally**: Organize one section at a time for large drives
5. **Regular maintenance**: Run cleanup periodically to maintain organization

## Troubleshooting

### "Credentials file not found"
Download `credentials.json` from Google Cloud Console and place in project root.

### "Permission denied" errors
Ensure your OAuth credentials have appropriate Google Drive API scopes.

### "Rate limit exceeded" 
The tool includes automatic rate limiting, but for very large drives, you may need to run operations in smaller batches.

### API quota exceeded
Google Drive API has daily quotas. If exceeded, wait 24 hours or request quota increase.