#!/bin/bash
set -e

echo "Testing File Organizer Server..."

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s http://localhost:8080/health | python3 -m json.tool

echo -e "\n2. Testing debug endpoint..."
curl -s http://localhost:8080/debug | python3 -m json.tool

echo -e "\n3. Testing simple start service..."
curl -X POST http://localhost:8080/api/v1/start-simple &
CURL_PID=$!
sleep 5
if kill -0 $CURL_PID 2>/dev/null; then
    echo "Simple start is hanging, killing it..."
    kill $CURL_PID 2>/dev/null || true
    wait $CURL_PID 2>/dev/null || true
    echo "Simple start was terminated due to timeout"
else
    wait $CURL_PID
    echo "Simple start completed"
fi

echo -e "\n4. Checking status after simple start..."
curl -s http://localhost:8080/api/v1/status | python3 -m json.tool

echo -e "\n5. Stopping service to test full start..."
curl -X POST http://localhost:8080/api/v1/stop &
STOP_PID=$!
sleep 3
if kill -0 $STOP_PID 2>/dev/null; then
    echo "Stop command hanging, trying force reset..."
    kill $STOP_PID 2>/dev/null || true
    wait $STOP_PID 2>/dev/null || true
    curl -X POST http://localhost:8080/api/v1/force-reset | python3 -m json.tool
else
    wait $STOP_PID
    echo "Stop command completed"
fi

echo -e "\n6. Checking status before full start..."
curl -s http://localhost:8080/api/v1/status | python3 -m json.tool

echo -e "\n7. Testing full start service..."
curl -X POST http://localhost:8080/api/v1/start &
CURL_PID=$!
sleep 10
if kill -0 $CURL_PID 2>/dev/null; then
    echo "Full start is hanging, killing it..."
    kill $CURL_PID 2>/dev/null || true
    wait $CURL_PID 2>/dev/null || true
    echo "Full start was terminated due to timeout"
else
    wait $CURL_PID
    echo "Full start completed"
fi

echo -e "\n8. Final status check..."
curl -s http://localhost:8080/api/v1/status | python3 -m json.tool

echo -e "\n9. Final logs check..."
curl -s http://localhost:8080/api/v1/logs | python3 -m json.tool | head -20

echo -e "\n10. Testing file modification detection..."
if [ "$(curl -s http://localhost:8080/api/v1/status | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")" = "running" ]; then
    echo "Service is running, testing file rename..."
    curl -X POST http://localhost:8080/api/v1/test/rename \
      -H "Content-Type: application/json" \
      -d '{"original_name": "test.pdf", "new_name": "Contract_TestClient_2024-01-15_signed.pdf"}' | python3 -m json.tool
    
    echo -e "\nWaiting for file processing..."
    sleep 5
    
    echo -e "\nChecking recent files..."
    curl -s http://localhost:8080/api/v1/files/recent | python3 -m json.tool
else
    echo "Service not running, skipping file test"
fi

echo -e "\nTest complete."
