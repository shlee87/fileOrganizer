# Signed PDF File Organizer

Automatically organizes signed PDF documents from a workplace folder into structured destination folders based on filename metadata.

## Installation

1. Install Python 3.10+ if not already installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage
```bash
python signed_watcher.py /path/to/workplace /path/to/destination
```

### Options
- `--dry-run`: Log actions without actually moving files
- `--stability-timeout SECONDS`: Wait time for file size to stabilize (default: 10.0)
- `--log-file PATH`: Log to file instead of console

### Example
```bash
# Dry run to test configuration
python signed_watcher.py ~/workplace ~/organized --dry-run --log-file watcher.log

# Run normally
python signed_watcher.py ~/workplace ~/organized --log-file watcher.log
```

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
python -m unittest test_signed_watcher.py -v
```

## Background Operation (macOS)

To run automatically on startup, create a launchd plist file. Example configuration can be found in the docs folder.