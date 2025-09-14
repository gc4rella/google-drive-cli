# Google Drive CLI Manager

A command-line tool to analyze, organize, and restructure your Google Drive folders efficiently.

## Features

- **Folder Structure Analysis**: Analyze your Drive organization and identify issues
- **Duplicate Detection**: Find duplicate files by name, size, and content with full paths
- **🧠 AI-Powered Analysis**: Use local LLM (Ollama) for intelligent restructuring suggestions
- **🚀 Smart Caching**: 10-100x faster subsequent operations, reduced API usage
- **Smart Reorganization**: Get context-aware suggestions for better folder structure
- **Project Boundary Detection**: Automatically identify logical project groupings
- **Intelligent Naming**: AI suggestions for better folder and file names
- **Batch Operations**: Safely reorganize files and folders in bulk
- **Preview Mode**: See changes before applying them

## Setup

### 1. Create Virtual Environment (Recommended)

**For Python 3.3+:**
```bash
# Create virtual environment
python -m venv drive-cli-env

# Activate virtual environment
# On macOS/Linux:
source drive-cli-env/bin/activate
# On Windows:
drive-cli-env\Scripts\activate
```

**For older Python versions with virtualenv:**
```bash
# Install virtualenv if needed
pip install virtualenv

# Create virtual environment
virtualenv drive-cli-env

# Activate virtual environment
# On macOS/Linux:
source drive-cli-env/bin/activate
# On Windows:
drive-cli-env\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Google Drive API credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one
   - Enable Google Drive API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download and save as `credentials.json`

### 4. Install and Setup Ollama (for AI features):
   ```bash
   # Install Ollama (visit https://ollama.ai for your OS)
   # On macOS:
   brew install ollama
   
   # Start Ollama service
   ollama serve
   
   # Pull the default model (in another terminal)
   ollama pull gpt-oss:20b
   ```

5. Run the tool:
   ```bash
   python main.py --help
   ```

### 4. Deactivate Virtual Environment (when done)

```bash
deactivate
```

## Usage

### Traditional Analysis
```bash
# Analyze your Drive structure (cached for 2h)
python main.py scan

# Find duplicates with full paths (uses cache)
python main.py duplicates

# Organize by file type
python main.py organize --preview
```

### 🧠 AI-Powered Features  
```bash
# Get intelligent analysis and suggestions
python main.py smart-analyze

# AI-powered reorganization suggestions
python main.py smart-organize

# Get AI suggestions for better folder names
python main.py smart-rename "old-folder-name" --folder-id "folder_id"
```

### 🚀 Caching Features
```bash
# Check cache status
python main.py cache-status

# Force fresh scan (ignores cache)
python main.py scan --force-refresh

# Clear cache
python main.py cache-clear

# Custom cache duration (6 hours)
python main.py scan --cache-ttl 6
```