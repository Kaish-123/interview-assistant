#!/bin/bash
# Setup WhatsApp Marketing Automation

echo "🚀 Setting up WhatsApp Marketing Automation..."
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p marketing_images
mkdir -p logs

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Grant Contacts access: System Preferences → Privacy → Contacts → Terminal"
echo "   2. Grant Accessibility access: System Preferences → Privacy → Accessibility → Terminal"
echo "   3. Put your marketing images in: $SCRIPT_DIR/marketing_images/"
echo "   4. Run the GUI: ./run_gui.sh"
echo "   5. Click 'Refresh Contacts' to sync from macOS Contacts"
echo ""
echo "🎉 Happy Marketing!"

