# Demo Files

This directory contains sample files for manually testing and demonstrating the file organizer.

## Structure

- **`workplace/`** - Sample PDF files with various naming patterns
- **`destination/`** - Example of organized file structure

## Usage

### Basic Demo
```bash
# From the backend directory
python src/signed_watcher.py demo/workplace demo/destination
```

### Dry Run Demo
```bash
# See what would happen without actually moving files
python src/signed_watcher.py demo/workplace demo/destination --dry-run
```

### With Logging
```bash
# Log actions to a file
python src/signed_watcher.py demo/workplace demo/destination --log-file demo.log
```

## Sample Files

The `workplace/` directory contains examples of:

- ✅ **Valid signed files**: Will be moved to organized folders
  - `contract_StartupAlpha_2024-08-21_signed.pdf`
  - `NDA_TechCorp_20240815_executed.pdf`
  - `employment_John_Doe_LLC_2024-06-15_fully_signed.pdf`
  - `service_ClientBeta_2024-07-30_final.pdf`

- ❌ **Files that won't be moved**:
  - `contract_StartupGamma_2024-08-20_draft.pdf` (not signed)
  - `invalid_filename.pdf` (doesn't match pattern)
  - `not_a_pdf.txt` (not a PDF file)

## Resetting Demo

To reset the demo files to their original state:

```bash
# Copy files back from fixtures
cp -r tests/fixtures/workplace/* demo/workplace/
```
