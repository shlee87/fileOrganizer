# Backend - Signed PDF File Organizer

Python backend service that watches a workplace folder and automatically moves signed PDFs to organized destination folders.

## Features

- Automatic file monitoring using watchdog
- PDF filename parsing based on naming conventions
- Organized file structure creation
- Configurable file patterns and destinations

## Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Set up Python version (if using pyenv):
   ```bash
   pyenv local 3.13.0  # or your preferred Python 3.10+ version
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the file organizer:
```bash
python src/signed_watcher.py demo/workplace demo/destination
```

### Command Options
```bash
# Dry run to test configuration
python src/signed_watcher.py demo/workplace demo/destination --dry-run

# With custom timeout and logging
python src/signed_watcher.py demo/workplace demo/destination --stability-timeout 5.0 --log-file watcher.log
```

## File Structure

- `src/` - Source code files
- `tests/` - Test files and fixtures
  - `fixtures/` - Test data (sample files for automated tests)
- `demo/` - Demo files for manual testing and demonstrations
- `requirements.txt` - Python dependencies
- `requirements-dev.txt` - Development dependencies
- `pyproject.toml` - Project configuration
- `venv/` - Virtual environment

## Configuration

Environment variables can be set in the `.env` file.

## Testing

The backend includes comprehensive unit tests to ensure code quality and reliability.

### Test Structure

```
backend/
├── tests/
│   ├── __init__.py
│   └── test_signed_watcher.py    # Tests for main module
├── src/
│   ├── __init__.py
│   └── signed_watcher.py         # Main application code
└── requirements-dev.txt          # Development dependencies
```

### Running Tests

#### Option 1: Using unittest (built-in)
```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test class
python -m unittest tests.test_signed_watcher.TestFilenameParser -v

# Run specific test method
python -m unittest tests.test_signed_watcher.TestFilenameParser.test_parse_valid_filename_with_dashes -v
```

#### Option 2: Using pytest (recommended)
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific tests
pytest tests/test_signed_watcher.py::TestFilenameParser -v
```

#### Option 3: Using the test runner script
```bash
# Run the comprehensive test suite
./run_tests.sh
```

### Test Coverage

The test suite covers:

- **FilenameParser**: Filename parsing, status detection, path normalization
- **FileStabilityChecker**: File stability detection
- **PDFMover**: File moving logic, dry-run mode, duplicate handling
- **PDFWatchHandler**: File system event handling

### Writing New Tests

When adding new features:

1. Add test methods to existing test classes or create new test classes
2. Follow the naming convention: `test_<functionality>`
3. Use descriptive docstrings
4. Test both success and failure cases
5. Use mocks for external dependencies

Example:
```python
def test_new_feature(self):
    """Test description of what this test validates."""
    # Arrange
    input_data = "test_input"
    
    # Act
    result = MyClass.new_feature(input_data)
    
    # Assert
    self.assertEqual(result, expected_output)
```
