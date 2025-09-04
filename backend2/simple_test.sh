#!/bin/bash

echo "Simple File Modification Test..."

# 1. Check if server is running
echo "1. Checking server health..."
if curl -s http://localhost:8080/health > /dev/null; then
    curl -s http://localhost:8080/health | python3 -m json.tool
else
    echo "Server not running. Please start with: python src/server.py"
    exit 1
fi

# 2. Start the service (avoid the hanging stop issue)
echo -e "\n2. Starting file monitoring service..."
curl -s -X POST http://localhost:8080/api/v1/start | python3 -m json.tool

# 3. Check status
echo -e "\n3. Checking service status..."
curl -s http://localhost:8080/api/v1/status | python3 -m json.tool

# 4. Create and test file rename
echo -e "\n4. Testing file modification detection..."
curl -s -X POST http://localhost:8080/api/v1/test/rename \
  -H "Content-Type: application/json" \
  -d '{"original_name": "test.pdf", "new_name": "Contract_TestClient_2024-01-15_signed.pdf"}' | python3 -m json.tool

# 5. Wait for processing
echo -e "\n5. Waiting for file processing..."
sleep 3

# 6. Check recent files
echo -e "\n6. Checking recent processed files..."
curl -s http://localhost:8080/api/v1/files/recent | python3 -m json.tool

# 7. Check logs
echo -e "\n7. Checking processing logs..."
curl -s http://localhost:8080/api/v1/logs | python3 -m json.tool | head -15

# 8. Check if file was moved to destination
echo -e "\n8. Checking destination directory..."
if [ -d "/tmp/destination" ]; then
    echo "Files in destination:"
    find /tmp/destination -name "*.pdf" -type f 2>/dev/null || echo "No PDF files found in destination"
else
    echo "Destination directory not found"
fi

echo -e "\nSimple test complete."
