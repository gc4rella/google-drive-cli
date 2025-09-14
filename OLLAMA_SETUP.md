# 🧠 AI-Powered Google Drive Manager - Ollama Setup

Your Google Drive CLI now has AI superpowers! Here's how to set up the local LLM integration.

## Why Ollama?

- **🔒 Privacy**: Everything runs locally - your data never leaves your machine
- **💰 Free**: No API costs, unlimited usage
- **🚀 Fast**: Optimized for local inference
- **🎯 Smart**: Context-aware folder organization suggestions

## Setup Steps

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [https://ollama.ai](https://ollama.ai)

### 2. Start Ollama Service
```bash
# Start in background
ollama serve

# Or if you want to see logs
ollama serve --verbose
```

### 3. Download AI Model
```bash
# Default: Powerful and intelligent
ollama pull gpt-oss:20b

# Alternative models:
# ollama pull llama3.2       # Faster but less capable
# ollama pull mistral        # Good for analysis
# ollama pull codellama      # Great for code organization  
# ollama pull llama3.1       # Alternative powerful model
```

### 4. Test Integration
```bash
# Activate your environment
source drive-cli-env/bin/activate

# Test AI features
python main.py smart-analyze
```

## AI Features Overview

### 🔍 `smart-analyze`
**What it does:**
- Analyzes your entire Drive structure with AI
- Identifies duplicate folder patterns (like duplicate project folders)
- Suggests logical project groupings
- Detects naming inconsistencies
- Provides confidence scores for suggestions

**Example output:**
```
💡 1. Consolidate Duplicate Projects
Merge Work/projects/duplicate-project folders - they appear to be the same project
Confidence: ███████████ 95%

Actions:
  • Merge content from both duplicate folders
  • Keep the folder with more recent files
  • Archive or delete the duplicate

💡 2. Create Academic Hierarchy
Group all research-related content under Academic/Research structure
Confidence: █████████ 85%
```

### 🧠 `smart-organize`
**What it does:**
- Provides AI-guided reorganization suggestions
- Plans folder moves and renames
- Suggests project-based organization
- (Note: Currently shows suggestions only, execution coming soon)

### ✏️ `smart-rename`
**What it does:**
- Suggests better names for folders based on their contents
- Follows naming conventions
- Considers context and project relationships

**Example:**
```bash
# Analyze a specific folder
python main.py smart-rename "misc" --folder-id "your-folder-id"

# Output: 
💡 Suggested name for 'misc': Academic-Resources
```

## Model Comparison

| Model | Speed | Quality | RAM Usage | Best For |
|-------|-------|---------|-----------|----------|
| gpt-oss:20b | ⚡ | ⭐⭐⭐⭐⭐ | 12GB | **Default - Best overall** |
| llama3.2 | ⚡⚡⚡ | ⭐⭐⭐ | 2GB | Fast, lightweight |
| mistral | ⚡⚡ | ⭐⭐⭐⭐ | 4GB | Detailed analysis |
| llama3.1 | ⚡ | ⭐⭐⭐⭐⭐ | 8GB | Complex restructuring |

## Advanced Usage

### Custom Models
```bash
# Use different model
python main.py smart-analyze --model llama3.2

# Use the default (most capable)
python main.py smart-analyze --model gpt-oss:20b

# List available models
ollama list
```

### Targeted Analysis
```bash
# Analyze specific folder
python main.py smart-analyze --folder-id "your-folder-id"

# Analyze work projects only
python main.py smart-analyze --folder-id "work-folder-id"
```

## Troubleshooting

### "Ollama connection failed"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```

### "Model not found"
```bash
# Pull the default model
ollama pull gpt-oss:20b

# Check available models
ollama list
```

### "Out of memory"
```bash
# Use smaller, faster model (needs only 2GB RAM)
python main.py smart-analyze --model llama3.2

# Or close other applications to free RAM for gpt-oss:20b
```

## What's Next?

The AI integration will continue to evolve:

1. **Smart Execution**: Actually perform AI-suggested moves
2. **Learning**: Remember your preferences
3. **Batch Processing**: Handle large reorganizations intelligently
4. **Content Analysis**: Analyze file contents for better categorization

## Privacy Note

🔒 **Your data stays local!** Unlike cloud AI services:
- No data sent to external servers
- No usage tracking
- No subscription fees
- Full control over your information

Ready to let AI revolutionize your Google Drive organization? 🚀