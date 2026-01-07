#!/bin/bash

# Script to package the browser extension for publishing
# Creates a zip file ready for upload to browser extension stores

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTENSION_DIR="$SCRIPT_DIR/extension"
OUTPUT_FILE="$SCRIPT_DIR/picture-of-the-day-extension.zip"
TEMP_DIR=$(mktemp -d)

echo "Packaging browser extension..."

# Check if extension directory exists
if [ ! -d "$EXTENSION_DIR" ]; then
    echo "Error: extension directory not found!"
    exit 1
fi

# Create temporary directory for packaging
echo "Creating package..."

# Copy extension files to temp directory, excluding unwanted files
if command -v rsync &> /dev/null; then
rsync -a --exclude='.DS_Store' \
         --exclude='.git*' \
         --exclude='*.swp' \
         --exclude='*.swo' \
         --exclude='*~' \
         --exclude='README*.md' \
         --exclude='*.production.json' \
         --exclude='*.production.js' \
         --exclude='__tests__' \
         --exclude='node_modules' \
         --exclude='jest.setup.js' \
         --exclude='package.json' \
         --exclude='package-lock.json' \
         --exclude='prepare-dev.sh' \
         --exclude='restore-dev.sh' \
         --exclude='.test-backup' \
         --exclude='store-assets' \
         "$EXTENSION_DIR/" "$TEMP_DIR/"
else
    # Fallback: use cp and then clean up
    cp -r "$EXTENSION_DIR"/* "$TEMP_DIR/" 2>/dev/null || true
fi

# Clean up excluded files and directories (works for both rsync and cp)
find "$TEMP_DIR" -name ".DS_Store" -delete 2>/dev/null || true
find "$TEMP_DIR" -name ".git*" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "*.swp" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "*.swo" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "*~" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "README*.md" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "*.production.json" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "*.production.js" -delete 2>/dev/null || true
find "$TEMP_DIR" -type d -name "__tests__" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -name "jest.setup.js" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "package.json" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "package-lock.json" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "prepare-dev.sh" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "restore-dev.sh" -delete 2>/dev/null || true
find "$TEMP_DIR" -type d -name ".test-backup" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -type d -name "store-assets" -exec rm -rf {} + 2>/dev/null || true

# Replace manifest.json with production version for packaging
if [ -f "$EXTENSION_DIR/manifest.production.json" ]; then
    echo "Using production manifest (without localhost)..."
    cp "$EXTENSION_DIR/manifest.production.json" "$TEMP_DIR/manifest.json"
    # Remove the production.json file from temp dir (it's no longer needed)
    find "$TEMP_DIR" -name "*.production.json" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "*.production.js" -delete 2>/dev/null || true
else
    echo "Warning: manifest.production.json not found, using manifest.json (may include localhost)"
    # Still remove any production.json files from temp dir
    find "$TEMP_DIR" -name "*.production.json" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "*.production.js" -delete 2>/dev/null || true
fi

# Replace config.js with production version for packaging
if [ -f "$EXTENSION_DIR/config.production.js" ]; then
    echo "Using production config..."
    cp "$EXTENSION_DIR/config.production.js" "$TEMP_DIR/config.js"
    # Remove the production.js file from temp dir (it's no longer needed)
    find "$TEMP_DIR" -name "*.production.js" -delete 2>/dev/null || true
else
    echo "Warning: config.production.js not found, using config.js (may include localhost)"
    # Still remove any production.js files from temp dir
    find "$TEMP_DIR" -name "*.production.js" -delete 2>/dev/null || true
fi

# Check for required files
REQUIRED_FILES=("manifest.json" "config.js" "newtab.html" "newtab.js" "styles.css")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$TEMP_DIR/$file" ]; then
        echo "Warning: Required file $file not found!"
    fi
done

# Final cleanup - ensure test files are removed before zipping
# Use explicit paths to ensure files are removed
[ -d "$TEMP_DIR/__tests__" ] && rm -rf "$TEMP_DIR/__tests__"
[ -d "$TEMP_DIR/node_modules" ] && rm -rf "$TEMP_DIR/node_modules"
[ -f "$TEMP_DIR/jest.setup.js" ] && rm -f "$TEMP_DIR/jest.setup.js"
[ -f "$TEMP_DIR/package.json" ] && rm -f "$TEMP_DIR/package.json"
[ -f "$TEMP_DIR/package-lock.json" ] && rm -f "$TEMP_DIR/package-lock.json"
[ -f "$TEMP_DIR/prepare-dev.sh" ] && rm -f "$TEMP_DIR/prepare-dev.sh"
[ -f "$TEMP_DIR/restore-dev.sh" ] && rm -f "$TEMP_DIR/restore-dev.sh"
[ -d "$TEMP_DIR/.test-backup" ] && rm -rf "$TEMP_DIR/.test-backup"
[ -d "$TEMP_DIR/store-assets" ] && rm -rf "$TEMP_DIR/store-assets"

# Check for icons (now in icons/ subdirectory)
if [ ! -f "$TEMP_DIR/favicon.ico" ] && [ ! -d "$TEMP_DIR/icons" ]; then
    echo "Warning: No icon files found. Consider adding icons/icon-16.png, icons/icon-48.png, and icons/icon-128.png"
fi

# Verify test files are excluded
if [ -d "$TEMP_DIR/__tests__" ] || [ -d "$TEMP_DIR/node_modules" ]; then
    echo "Warning: Test files or node_modules found in package. These should be excluded."
fi

# Create zip file
cd "$TEMP_DIR"
zip -r "$OUTPUT_FILE" . -q

# Clean up
rm -rf "$TEMP_DIR"

# Get file size
FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo "Extension packaged successfully!"
echo "Output: $OUTPUT_FILE"
echo "Size: $FILE_SIZE"
echo ""
echo "Files included:"
unzip -l "$OUTPUT_FILE" | tail -n +4 | head -n -2 | awk '{print "   " $4}'
echo ""
echo "Ready to upload to browser extension stores!"

