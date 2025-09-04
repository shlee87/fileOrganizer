# API Specification
Project: Signed-PDF File Organizer - Backend API for UI
Author: Seonghoon Yi  
Date: 2025-01-21

## Overview
RESTful API specification for the web UI to interact with the file organizer backend. The backend Python application will be extended with a Flask/FastAPI web server to provide these endpoints.

## Base Configuration
- **Base URL**: `http://localhost:8080/api/v1`
- **Content-Type**: `application/json`
- **Authentication**: None (MVP - local deployment only)
- **CORS**: Enabled for `http://localhost:3000` (UI development server)

## Error Response Format
All error responses follow this structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error context",
    "timestamp": "2025-01-21T10:30:00Z"
  }
}
```

## Endpoints

### 1. Service Control

#### GET /service/status
Get current service status and health information.

**Response** (200 OK):
```json
{
  "status": "running|stopped|error",
  "uptime_seconds": 3600,
  "last_started": "2025-01-21T09:00:00Z",
  "last_error": null,
  "version": "1.0.0",
  "workplace_accessible": true,
  "destination_accessible": true,
  "files_in_queue": 2,
  "files_processed_today": 15
}
```

#### POST /service/start
Start the file watcher service.

**Request Body**:
```json
{
  "config_path": "/optional/path/to/config.json"
}
```

**Response** (200 OK):
```json
{
  "message": "Service started successfully",
  "started_at": "2025-01-21T10:30:00Z"
}
```

**Error Responses**:
- 409 Conflict: Service already running
- 400 Bad Request: Invalid configuration

#### POST /service/stop
Stop the file watcher service gracefully.

**Request Body**:
```json
{
  "force": false,
  "timeout_seconds": 30
}
```

**Response** (200 OK):
```json
{
  "message": "Service stopped successfully",
  "stopped_at": "2025-01-21T10:30:00Z",
  "files_processed_before_stop": 3
}
```

#### POST /service/restart
Restart the service with current or new configuration.

**Response** (200 OK): Same as start endpoint

### 2. Configuration Management

#### GET /config
Get current configuration settings.

**Response** (200 OK):
```json
{
  "workplace_path": "/Users/john/Documents/workplace",
  "destination_root": "/Users/john/Documents/organized", 
  "stable_wait_seconds": 5,
  "dry_run_mode": false,
  "status_keywords": ["signed", "executed", "final"],
  "filename_pattern": "^(?P<doc>.+?)_(?P<client>.+?)_(?P<date>\\d{4}-?\\d{2}-?\\d{2})_(?P<status>.+?)\\.pdf$",
  "log_level": "INFO",
  "config_file_path": "/path/to/current/config.json"
}
```

#### POST /config
Update configuration settings. Service restart required for some changes.

**Request Body**:
```json
{
  "workplace_path": "/new/workplace/path",
  "destination_root": "/new/destination/path",
  "stable_wait_seconds": 10,
  "dry_run_mode": true,
  "status_keywords": ["signed", "executed", "final", "completed"],
  "log_level": "DEBUG"
}
```

**Response** (200 OK):
```json
{
  "message": "Configuration updated successfully",
  "restart_required": true,
  "validation_warnings": [
    "Workplace path does not exist: /new/workplace/path"
  ]
}
```

#### POST /config/validate
Validate configuration without applying changes.

**Request Body**: Same as POST /config

**Response** (200 OK):
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Destination directory will be created: /new/destination/path"
  ]
}
```

### 3. File Operations

#### GET /files/recent
Get recently processed and pending files.

**Query Parameters**:
- `limit`: number of files (default: 50, max: 200)
- `status`: filter by status (`pending|processed|failed|skipped`)
- `since`: ISO timestamp for files after this time
- `client`: filter by client name
- `document`: filter by document type

**Response** (200 OK):
```json
{
  "files": [
    {
      "id": "file_001", 
      "original_path": "/workplace/contract_acme_2025-01-15_signed.pdf",
      "destination_path": "/dest/acme/contract/Signed/contract_acme_2025-01-15_signed.pdf",
      "status": "processed",
      "detected_at": "2025-01-21T10:25:00Z",
      "processed_at": "2025-01-21T10:25:05Z",
      "file_size_bytes": 2048576,
      "error_message": null,
      "parsed_metadata": {
        "document": "contract",
        "client": "acme", 
        "date": "2025-01-15",
        "status": "signed",
        "normalized_client": "acme",
        "normalized_document": "contract"
      }
    }
  ],
  "total": 15,
  "has_more": false
}
```

#### POST /files/reprocess
Manually reprocess a specific file.

**Request Body**:
```json
{
  "file_path": "/workplace/contract_acme_2025-01-15_signed.pdf",
  "force": false
}
```

**Response** (200 OK):
```json
{
  "message": "File queued for reprocessing",
  "processing_id": "proc_001",
  "estimated_completion": "2025-01-21T10:30:30Z"
}
```

#### GET /files/preview
Preview what would happen to files currently in workplace.

**Query Parameters**:
- `dry_run`: always true for this endpoint
- `include_non_matching`: show files that wouldn't be processed

**Response** (200 OK):
```json
{
  "files": [
    {
      "file_path": "/workplace/contract_acme_2025-01-15_signed.pdf",
      "would_process": true,
      "reason": "Matches pattern and contains signed status",
      "destination_path": "/dest/acme/contract/Signed/contract_acme_2025-01-15_signed.pdf",
      "conflicts": false,
      "parsed_metadata": { /* same as above */ }
    },
    {
      "file_path": "/workplace/document_without_status.pdf", 
      "would_process": false,
      "reason": "No signed status keyword found",
      "destination_path": null,
      "conflicts": false,
      "parsed_metadata": null
    }
  ],
  "summary": {
    "total_files": 2,
    "would_process": 1,
    "would_skip": 1,
    "conflicts": 0
  }
}
```

### 4. Monitoring and Logs

#### GET /logs
Get application logs with filtering.

**Query Parameters**:
- `level`: filter by log level (`DEBUG|INFO|WARNING|ERROR`)
- `limit`: number of entries (default: 100, max: 1000)
- `since`: ISO timestamp to get logs after
- `search`: text search in log messages

**Response** (200 OK):
```json
{
  "logs": [
    {
      "timestamp": "2025-01-21T10:30:00Z",
      "level": "INFO",
      "message": "File processed successfully", 
      "module": "mover",
      "file_path": "/workplace/contract_acme_2025-01-15_signed.pdf",
      "extra_data": {
        "processing_time_ms": 1250,
        "destination": "/dest/acme/contract/Signed/..."
      }
    }
  ],
  "total": 1543,
  "has_more": true
}
```

#### GET /stats
Get processing statistics and metrics.

**Query Parameters**:
- `period`: time period (`today|week|month|all`)

**Response** (200 OK):
```json
{
  "period": "today",
  "summary": {
    "files_processed": 15,
    "files_failed": 2, 
    "files_skipped": 5,
    "total_size_bytes": 52428800,
    "avg_processing_time_ms": 1100
  },
  "by_client": {
    "acme": {"processed": 8, "failed": 1},
    "beta_corp": {"processed": 4, "failed": 0},
    "gamma_llc": {"processed": 3, "failed": 1}
  },
  "by_document_type": {
    "contract": {"processed": 10, "failed": 1},
    "amendment": {"processed": 3, "failed": 1}, 
    "agreement": {"processed": 2, "failed": 0}
  },
  "hourly_breakdown": [
    {"hour": "09:00", "processed": 5, "failed": 0},
    {"hour": "10:00", "processed": 10, "failed": 2}
  ]
}
```

### 5. WebSocket Events (Real-time Updates)

**Connection**: `ws://localhost:8080/api/v1/events`

**Event Types**:

```json
{
  "type": "file.detected",
  "timestamp": "2025-01-21T10:30:00Z",
  "data": {
    "file_path": "/workplace/contract_acme_2025-01-15_signed.pdf",
    "file_size": 2048576
  }
}

{
  "type": "file.processed", 
  "timestamp": "2025-01-21T10:30:05Z",
  "data": {
    "file_path": "/workplace/contract_acme_2025-01-15_signed.pdf",
    "destination_path": "/dest/acme/contract/Signed/contract_acme_2025-01-15_signed.pdf",
    "processing_time_ms": 1250,
    "parsed_metadata": { /* ... */ }
  }
}

{
  "type": "service.status_changed",
  "timestamp": "2025-01-21T10:30:00Z", 
  "data": {
    "old_status": "stopped",
    "new_status": "running"
  }
}
```

## Implementation Notes

### Rate Limiting
- 100 requests per minute per IP for REST endpoints
- WebSocket connections limited to 5 per IP
- Large file operations may take longer than typical HTTP timeouts

### Caching
- Configuration cached in memory, refreshed on file changes
- Recent files list cached for 30 seconds
- Statistics cached for 5 minutes

### Backwards Compatibility
- All endpoints versioned (`/api/v1/`)
- CLI interface remains unchanged
- Configuration file format compatible with existing backend
