# File Organizer

A full-stack application for automatically organizing signed PDF documents. The system watches a workplace folder and moves signed PDFs to organized destination folders based on filename metadata.

## Project Structure

- **`backend/`** - Python backend service for file monitoring and organization
- **`frontend/`** - Web interface for monitoring and configuration (coming soon)
- **`docs/`** - Documentation and project resources

## Quick Start

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python 3.10+ if not already installed
3. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage
```bash
cd backend
python src/signed_watcher.py test_workplace test_destination
```

### Options
- `--dry-run`: Log actions without actually moving files
- `--stability-timeout SECONDS`: Wait time for file size to stabilize (default: 10.0)
- `--log-file PATH`: Log to file instead of console

### Example
```bash
# Dry run to test configuration
python src/signed_watcher.py test_workplace test_destination --dry-run --log-file watcher.log

# Run normally
python src/signed_watcher.py test_workplace test_destination --log-file watcher.log
```

## Frontend

The frontend web interface is planned for future development. See `frontend/README.md` for more details.

## Filename Pattern

Files must match this pattern to be processed:
```
<document>_<client>_<YYYY[-]MM[-]DD>_<status>.pdf
```

Examples:
- `contract_ClientName_2024-01-15_signed.pdf`
- `NDA_Startup_Inc_20240115_executed.pdf`
- `agreement_test_client_2024-12-31_final.pdf`

## Signed Status Detection

Files are considered "signed" if the status contains:
- `signed`
- `executed` 
- `final`
- `_signed` (anywhere in status)

Case-insensitive matching.

## Destination Structure

Signed files are moved to:
```
DEST_ROOT/<document_form>/<client>/<date>/<status>/<original-filename>
```

Example paths:
- `contract/StartupAlpha/2024-08-21/signed/contract_StartupAlpha_2024-08-21_signed.pdf`
- `NDA/TechCorp/20240815/executed/NDA_TechCorp_20240815_executed.pdf`

Path segments are normalized (spaces → underscores, unsafe chars removed).

## Features

- **File stability checking**: Waits for file copy to complete before processing
- **Duplicate handling**: Appends timestamp to filename if destination exists
- **Dry run mode**: Test configuration without moving files
- **Comprehensive logging**: All actions and errors logged with timestamps
- **Non-recursive watching**: Only monitors the workplace folder directly

## Testing

Run unit tests:
```bash
cd backend
python -m unittest discover tests -v
```

## Development

For detailed backend documentation, see `backend/README.md`.
For frontend development plans, see `frontend/README.md`.