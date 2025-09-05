#!/bin/bash
# Test runner script for the backend

echo "Running tests for File Organizer Backend..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Install test dependencies
echo "Installing test dependencies..."
pip install -r requirements-dev.txt

# Run tests with different options
echo ""
echo "=== Running Unit Tests ==="
python -m pytest tests/ -v

echo ""
echo "=== Running Tests with Coverage ==="
python -m pytest tests/ --cov=src --cov-report=term-missing

echo ""
echo "=== Running specific test file ==="
echo "To run specific tests:"
echo "  python -m pytest tests/test_signed_watcher.py -v"
echo "  python -m pytest tests/test_signed_watcher.py::TestFilenameParser -v"
echo "  python -m pytest tests/test_signed_watcher.py::TestFilenameParser::test_parse_valid_filename_with_dashes -v"

echo ""
echo "=== Alternative: Using unittest ==="
echo "python -m unittest discover tests -v"
