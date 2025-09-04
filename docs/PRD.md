# Product Requirements Document (PRD)
Project: Signed-PDF File Organizer
Author: Seonghoon Yi
Date: 2025-08-21
Last Updated: 2025-01-21

## 1. Purpose / Summary
Automate moving of signed PDF documents from a single "workplace" drop folder into a structured destination folder based solely on filename metadata. Move occurs only when the filename indicates a signed status (e.g., contains `_signed`, `signed`, `executed`, `final`).

**Current Status**: Backend MVP implemented. Preparing for UI development phase.

## 2. Background / Context
Client: LA-based attorney who onboards SK startups into US (Delaware). Current pain: manual document organization. Files are generated and dropped into one workplace folder; signed PDFs should be auto-sorted to reduce manual work.

**Implementation Context**: Python-based backend with file watcher. UI layer to be added for better control and monitoring.

## 3. Goals (MVP)
- Detect new or renamed PDF files in workplace.
- Parse filename of pattern: `<document>_<client>_<YYYY[-]MM[-]DD>_<status>.pdf`.
- If status indicates signed, move file to: `DEST_ROOT/<client>/<document>/Signed/<original-filename>`.
- Ensure robustness: only PDFs processed, wait for copy to complete, handle duplicates, logging, dry-run mode.

## 4. Scope
In scope (Backend - IMPLEMENTED):
- Watch a single workplace folder (non-recursive).
- Only process .pdf files.
- Support status detection: `signed`, `executed`, `final` (case-insensitive) and explicit `_signed` tag.
- Destination folder structure derived from parsed filename segments.
- Duplicate handling: append timestamp to filename.
- Safe move after file size is stable.
- Logging for operations and failures.
- Command-line interface with dry-run mode.

In scope (UI - PLANNED):
- Web-based control panel for starting/stopping service
- Configuration management interface
- Real-time monitoring of file processing
- Log viewing and filtering
- File processing history and statistics
- Manual file reprocessing capability

Out of scope (MVP):
- Cloud storage or e-signature integrations.
- Role-based access controls and encryption at rest (can be added later).
- Full-text indexing or document templating.
- Multi-user concurrent access.

## 5. Functional Requirements
FR-1: Watch workplace for file creation and move/rename events.
FR-2: Accept only files with `.pdf` extension.
FR-3: Parse filename by regex: `^(?P<doc>.+?)_(?P<client>.+?)_(?P<date>\d{4}-?\d{2}-?\d{2})_(?P<status>.+?)\.pdf$` (case-insensitive).
FR-4: Determine signed status if `status` contains any of `signed`, `executed`, `final` or includes `_signed`.
FR-5: Wait until file size is stable (configurable timeout) before acting.
FR-6: Move signed files to `DEST_ROOT/<client>/<doc>/Signed/`.
FR-7: Normalize folder segment strings (replace unsafe chars, spaces -> underscores).
FR-8: If destination filename conflicts, append epoch timestamp before extension.
FR-9: Provide `--dry-run` mode to log intended actions without moving files.
FR-10: Log every action and error to a file with timestamps.

## 6. Non-Functional Requirements
NFR-1: Must run on macOS (support launch via launchd or manual).
NFR-2: Low CPU/memory footprint (simple Python script acceptable).
NFR-3: Reliable for files up to typical contract sizes (tens of MB).
NFR-4: Fail-safe: do not delete original files on errors; preserve workplace contents on failure.

## 7. Acceptance Criteria
- AC-1: When a valid signed PDF is created or renamed into workplace, it appears in correct destination path.
- AC-2: Non-signed PDFs remain untouched in workplace.
- AC-3: Duplicate names are not overwritten; new file saved with timestamp suffix.
- AC-4: Actions logged; dry-run produces the same log entries without moving files.
- AC-5: Script tolerates a file copy time up to configured timeout and processes after size stabilizes.

## 8. User Stories
- As an attorney, I want signed PDFs to automatically move to a client/document/Signed folder so I don't manually sort them.
- As an operator, I want a dry-run to verify behavior before enabling moves.
- As an admin, I want logs to audit moved files and troubleshoot failures.

## 9. Implementation Approach
**Backend (IMPLEMENTED)**:
Tech stack:
- Python 3.10+
- watchdog for filesystem events
- shutil / pathlib for moves
- logging module for logs
- argparse for CLI

Key modules:
- watcher: observe workplace (FileSystemEventHandler)
- parser: filename regex + normalization
- mover: stability check + move + duplicate handling
- CLI: args for workplace path, dest root, dry-run, stable-wait

**UI Layer (PLANNED)**:
Tech stack:
- Backend API: Flask/FastAPI web server extension
- Frontend: React/Vue.js or simple HTML/JS
- Communication: REST API + WebSocket for real-time updates
- Data persistence: JSON config files + optional SQLite for logs/history

API Requirements:
- RESTful endpoints for configuration, service control, file operations
- WebSocket for real-time status updates
- JSON-based request/response format
- Error handling with appropriate HTTP status codes

## 10. Risks & Mitigations
- Risk: Partial uploads trigger premature moves. Mitigation: wait for file size stable.
- Risk: Filename variations not captured. Mitigation: log unmatched names and provide list to client for naming standardization; configurable regex later.
- Risk: Large number of files cause backlog. Mitigation: non-recursive watch and batch processing option later.

## 11. Metrics / Success Measures
- Reduction in manual file-sorting time (qualitative client feedback).
- 100% of signed PDFs moved correctly within 60s of copy completion in tests.
- Zero overwrites of existing destination files.

## 12. Open Questions
1. Confirm exact accepted date format(s) and whether date can be optional.
2. Confirm canonical mapping for client names (should surname punctuation be preserved?).
3. Desired destination root path and whether multi-root support is needed.
4. Should we keep an audit DB (SQLite) for undo/history now or later?

## 13. Milestones & Estimated Effort (MVP)
- M1 (1 day): Parser and unit tests for filename parsing.
- M2 (2 days): Watcher script with stability check, move logic, duplicate handling, logging, dry-run.
- M3 (0.5 day): Basic README and sample launchd plist.
- M4 (1 day optional): Add SQLite audit log and simple rollback command.

## 14. Next Steps
- Confirm answers to Open Questions.
- Approve MVP milestone plan.
- I can implement M1+M2 and provide unit tests and a launchd plist. Which next step

## 15. Backend-UI Integration Requirements
**Configuration Management**:
- UI must read/write same config format as backend CLI
- Backend must support config reload without restart
- Validation of paths and settings before applying

**Service Control**:
- Start/stop/restart file watcher from UI
- Real-time service status monitoring
- Process health checks and error reporting

**File Processing Monitoring**:
- Live view of files being processed
- Processing history with filtering capabilities
- Manual reprocessing of failed files
- Preview mode to see what files would be processed

**Logging Integration**:
- Structured logging format for UI consumption
- Log level filtering and search capabilities
- Export logs for troubleshooting

## 16. Data Models for UI Integration
**Configuration Object**:
```json
{
  "workplace_path": "/path/to/workplace",
  "destination_root": "/path/to/dest", 
  "stable_wait_seconds": 5,
  "dry_run_mode": false,
  "status_keywords": ["signed", "executed", "final"],
  "filename_pattern": "regex_pattern"
}
```

**File Processing Record**:
```json
{
  "id": "unique_id",
  "file_path": "/original/path/file.pdf",
  "destination_path": "/dest/path/file.pdf",
  "status": "pending|processed|failed",
  "processed_at": "2025-01-21T10:30:00Z",
  "error_message": "error details if failed",
  "parsed_metadata": {
    "document": "contract",
    "client": "acme_corp", 
    "date": "2025-01-15",
    "status": "signed"
  }
}
```

**Service Status**:
```json
{
  "status": "running|stopped|error",
  "uptime_seconds": 3600,
  "last_error": null,
  "files_processed_today": 15,
  "workplace_accessible": true,
  "destination_accessible": true
}
```

## 17. Next Steps for UI Development
1. **Backend API Extension**: Add Flask/FastAPI server to existing backend
2. **API Specification**: Define RESTful endpoints and WebSocket events  
3. **UI Requirements Document**: Detailed UI/UX requirements
4. **Frontend Architecture**: Choose technology stack and implementation approach
5. **Integration Testing**: Ensure seamless backend-UI communication

## 18. Backward Compatibility
- CLI interface must remain functional alongside UI
- Configuration file format must support both CLI and UI access
- Existing logging format should be enhanced but not broken
- Service can run in CLI-only mode without UI components