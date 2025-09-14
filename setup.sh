#!/bin/bash

# Google Drive CLI Manager Setup Script
# This script sets up the virtual environment and dependencies

echo "🚀 Setting up Google Drive CLI Manager..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ and try again."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment
echo "📦 Creating virtual environment..."
if python3 -m venv drive-cli-env; then
    echo "✅ Virtual environment created successfully"
else
    echo "❌ Failed to create virtual environment"
    echo "💡 Try: pip install virtualenv && virtualenv drive-cli-env"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source drive-cli-env/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
if pip install -r requirements.txt; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo
echo "🎉 Setup complete!"
echo
echo "📋 Next steps:"
echo "1. Activate the virtual environment:"
echo "   source drive-cli-env/bin/activate"
echo
echo "2. Set up Google Drive API credentials:"
echo "   python main.py setup"
echo
echo "3. Test the connection:"
echo "   python main.py test"
echo
echo "4. Start analyzing your Drive:"
echo "   python main.py scan"
echo
echo "💡 To deactivate the virtual environment later, just run: deactivate"