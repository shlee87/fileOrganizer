# Backend Architecture Documentation
Project: Signed-PDF File Organizer Backend
Author: Seonghoon Yi
Date: 2025-01-21

## Overview
The backend is implemented as a Python application that watches a workplace directory for PDF files and automatically organizes them based on filename patterns. This document describes the current architecture and interfaces needed for UI integration.

## Core Components

### 1. File System Watcher (`watcher.py`)
- Uses `watchdog` library for filesystem event monitoring
- Monitors single workplace directory (non-recursive)
- Filters for PDF files only
- Handles file creation, modification, and move events
- Implements stability checking before processing

### 2. Filename Parser (`parser.py`)
- Regex-based filename parsing
- Pattern: `^(?P<doc>.+?)_(?P<client>.+?)_(?P<date>\d{4}-?\d{2}-?\d{2})_(?P<status>.+?)\.pdf$`
- Status keyword detection: "signed", "executed", "final"
- String normalization for filesystem safety
- Date format validation and normalization

### 3. File Mover (`mover.py`)
- Safe file moving with stability checks
- Destination path generation: `DEST_ROOT/<client>/<document>/Signed/`
- Duplicate handling with timestamp suffixes
- Atomic operations to prevent data loss
- Comprehensive error handling and rollback

### 4. Configuration Manager (`config.py`)
- JSON-based configuration storage
- Runtime configuration validation
- Default value management
- Environment variable overrides
- Hot-reload capability for UI integration

### 5. Logging System (`logging_config.py`)
- Structured logging with multiple levels
- File and console output
- JSON format for machine parsing
- Rotation and retention policies
- Audit trail for all file operations

## Data Flow
```
Workplace Directory → Watcher → Parser → Validator → Mover → Destination
                          ↓
                     Logger ← Config Manager
```

## Configuration Schema
```json
{
  "workplace_path": "/path/to/workplace",
  "destination_root": "/path/to/destination",
  "stable_wait_seconds": 5,
  "dry_run_mode": false,
  "status_keywords": ["signed", "executed", "final"],
  "filename_pattern": "regex_string",
  "log_level": "INFO",
  "log_file_path": "/path/to/logs/organizer.log"
}
```

## Event System for UI Integration
The backend emits events that the UI can subscribe to:

### File Processing Events
- `file.detected`: New PDF file found in workplace
- `file.parsing`: Attempting to parse filename
- `file.parsed`: Successfully parsed filename metadata
- `file.moving`: Starting file move operation
- `file.moved`: File successfully moved
- `file.failed`: Processing failed with error details
- `file.skipped`: File skipped (not signed status)

### Service Events
- `service.started`: File watcher service started
- `service.stopped`: Service stopped
- `service.error`: Service encountered error
- `config.updated`: Configuration changed
- `config.reloaded`: Configuration reloaded from file

## API Requirements for UI
The backend needs these additional components for UI integration:

### 1. Web Server Module
- Flask or FastAPI application
- RESTful API endpoints
- WebSocket support for real-time updates
- CORS configuration for web UI
- Request validation and error handling

### 2. State Management
- In-memory service state tracking
- File processing queue status
- Recent processing history
- Performance metrics collection

### 3. Database Layer (Optional)
- SQLite for persistent logging
- Processing history storage
- Configuration backup
- Audit trail maintenance

## Error Handling Strategy
1. **Graceful Degradation**: Service continues running despite individual file failures
2. **Comprehensive Logging**: All errors logged with context and stack traces
3. **User Notification**: Errors exposed via API for UI display
4. **Recovery Mechanisms**: Automatic retry for transient failures
5. **Safe Failure**: No data loss on errors, original files preserved

## Security Considerations
- **Path Validation**: Prevent directory traversal attacks
- **File Type Validation**: Strict PDF-only processing
- **Permission Checks**: Validate read/write access before operations
- **Input Sanitization**: Clean all user-provided paths and patterns
- **Resource Limits**: Prevent excessive memory/CPU usage

## Performance Characteristics
- **Memory Usage**: < 50MB typical, < 100MB with large queues
- **CPU Usage**: < 5% during normal operation
- **File Processing Time**: < 1 second per file for typical PDFs
- **Startup Time**: < 2 seconds for service initialization
- **Shutdown Time**: < 5 seconds with graceful queue completion

## Monitoring and Observability
- **Health Checks**: Service status endpoint for uptime monitoring
- **Metrics**: File processing counts, success/failure rates, timing
- **Alerts**: Configurable thresholds for error rates and processing delays
- **Debugging**: Verbose logging modes for troubleshooting

## Extension Points for UI
1. **Plugin System**: Allow custom filename patterns and processing rules
2. **Webhook Support**: External integrations for file processing events
3. **Batch Operations**: UI-triggered bulk reprocessing capabilities
4. **Preview Mode**: Dry-run simulation for UI configuration testing
5. **Export/Import**: Configuration and processing history backup/restore
