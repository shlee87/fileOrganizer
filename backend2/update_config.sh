#!/bin/bash

echo "Updating File Organizer configuration..."

WORKPLACE_PATH="/Users/seonghoonyi/Documents/projects/fileOrganizer/tests/fixtures/workplace"
DESTINATION_PATH="/Users/seonghoonyi/Documents/projects/fileOrganizer/tests/fixtures/destination"

# Create directories if they don't exist
mkdir -p "$WORKPLACE_PATH"
mkdir -p "$DESTINATION_PATH"

echo "Created directories:"
echo "  Workplace: $WORKPLACE_PATH"
echo "  Destination: $DESTINATION_PATH"

# Update configuration via API
echo "Updating server configuration..."
curl -X POST http://localhost:8080/api/v1/config \
  -H "Content-Type: application/json" \
  -d "{
    \"workplace_path\": \"$WORKPLACE_PATH\",
    \"destination_root\": \"$DESTINATION_PATH\"
  }" | python3 -m json.tool

echo -e "\nVerifying configuration..."
curl -s http://localhost:8080/api/v1/config | python3 -m json.tool

echo -e "\nConfiguration update complete!"
echo "Note: You may need to restart the service for changes to take effect."
