#!/bin/bash
# Script to fix the .env file on the server
# Removes the invalid GEMINI_API_KEY placeholder that causes errors

ENV_FILE="/opt/ArtinSmartRealty/.env"
BACKUP_FILE="/opt/ArtinSmartRealty/.env.bak"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Backup the file
cp "$ENV_FILE" "$BACKUP_FILE"
echo "✅ Backup created at $BACKUP_FILE"

# Check if the invalid key exists
if grep -q "GEMINI_API_KEY=your_gemini_api_key" "$ENV_FILE"; then
    echo "⚠️ Found invalid GEMINI_API_KEY placeholder. Removing..."
    
    # Remove the specific invalid line
    # We use sed to delete lines containing the specific bad string
    sed -i '/GEMINI_API_KEY=your_gemini_api_key/d' "$ENV_FILE"
    
    # Also remove the docker warning causing line if it exists as an empty var export
    # (Optional, but good cleanup)
    
    echo "✅ Removed invalid key entry."
else
    echo "✅ No invalid GEMINI_API_KEY placeholder found."
fi

# Verify keys exist
echo "🔍 Verifying valid keys..."
if grep -q "GEMINI_KEY_1=AIza" "$ENV_FILE"; then
    echo "✅ GEMINI_KEY_1 found."
else
    echo "⚠️ GEMINI_KEY_1 seems missing or invalid format."
    echo "Please ensure you have valid keys starting with AIza..."
fi

echo "🚀 Environment file fixed. Please restart the backend container:"
echo "docker-compose restart backend"
