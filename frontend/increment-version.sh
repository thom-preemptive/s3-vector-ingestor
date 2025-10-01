#!/bin/bash

# Auto-increment version script for Agent2 Document Ingestor
# This script increments the version number by 0.01 each deployment
# Uses Node.js instead of bc and jq for better compatibility

VERSION_FILE="src/version.json"

if [ -f "$VERSION_FILE" ]; then
    # Use Node.js to increment version
    node -e "
        const fs = require('fs');
        const versionFile = '$VERSION_FILE';
        
        try {
            const data = JSON.parse(fs.readFileSync(versionFile, 'utf8'));
            const currentVersion = parseFloat(data.version);
            const newVersion = (currentVersion + 0.01).toFixed(2);
            
            console.log('Current version:', currentVersion);
            console.log('New version:', newVersion);
            
            fs.writeFileSync(versionFile, JSON.stringify({version: newVersion}, null, 2));
            console.log('Version incremented successfully');
        } catch (error) {
            console.error('Error incrementing version:', error.message);
            process.exit(1);
        }
    "
else
    echo "Version file not found, creating with version 0.40"
    echo '{"version": "0.40"}' > $VERSION_FILE
fi