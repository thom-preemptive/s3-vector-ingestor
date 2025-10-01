#!/bin/bash

# Auto-increment version script for Agent2 Document Ingestor
# This script increments the version number by 0.01 each deployment

VERSION_FILE="src/version.json"

if [ -f "$VERSION_FILE" ]; then
    # Read current version
    CURRENT_VERSION=$(cat $VERSION_FILE | jq -r '.version')
    echo "Current version: $CURRENT_VERSION"
    
    # Increment version by 0.01
    NEW_VERSION=$(echo "$CURRENT_VERSION + 0.01" | bc -l)
    
    # Format to 2 decimal places
    NEW_VERSION=$(printf "%.2f" $NEW_VERSION)
    
    # Update version file
    echo "{\"version\": \"$NEW_VERSION\"}" > $VERSION_FILE
    
    echo "Version incremented to: $NEW_VERSION"
else
    echo "Version file not found, creating with version 0.40"
    echo "{\"version\": \"0.40\"}" > $VERSION_FILE
fi