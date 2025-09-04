"""
FastAPI server for the Signed PDF File Organizer.
Provides REST API endpoints and WebSocket for real-time updates.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
import uvicorn

from signed_watcher import (
    FilenameParser, 
    PDFMover, 
    FileStabilityChecker,
    PDFWatchHandler,
    setup_logging
)
from watchdog.observers import Observer


# Data Models
class ServiceStatus(BaseModel):
    status: str  # "running", "stopped", "error"
    uptime_seconds: Optional[int] = None
    files_processed_today: int = 0
    queue_size: int = 0
    last_error: Optional[str] = None


class Configuration(BaseModel):
    workplace_path: str
    destination_root: str
    stable_wait_seconds: float = 5.0
    dry_run_mode: bool = False
    status_keywords: List[str] = ["signed", "executed", "final"]
    filename_pattern: str = r'^(?P<doc>.+?)_(?P<client>.+?)_(?P<date>\d{4}-?\d{2}-?\d{2})_(?P<status>.+?)\.pdf$'
    log_level: str = "INFO"
    
    @field_validator('workplace_path', 'destination_root')
    @classmethod
    def validate_paths(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return str(path.absolute())


class FileInfo(BaseModel):
    id: str
    original_path: str
    destination_path: Optional[str] = None
    status: str  # "pending", "processed", "failed", "skipped"
    detected_at: datetime
    processed_at: Optional[datetime] = None
    file_size_bytes: int
    error_message: Optional[str] = None
    parsed_metadata: Optional[Dict[str, Any]] = None


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    module: str
    file_path: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class ProcessFileRequest(BaseModel):
    file_path: str
    force: bool = False


# Global state management
class ServiceManager:
    def __init__(self):
        self.status = "stopped"
        self.start_time: Optional[float] = None
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[PDFWatchHandler] = None
        self.files_processed_today = 0
        self.queue_size = 0
        self.last_error: Optional[str] = None
        self.configuration: Optional[Configuration] = None
        self.recent_files: List[FileInfo] = []
        self.log_entries: List[LogEntry] = []
        self.websocket_connections: List[WebSocket] = []
        
    async def start_service(self, config: Configuration):
        """Start the file watching service."""
        if self.status == "running":
            return
            
        try:
            self.configuration = config
            
            # Apply configured log level
            try:
                level = getattr(logging, config.log_level.upper(), None)
                if level is not None:
                    logging.getLogger().setLevel(level)
            except Exception:
                pass

            # Ensure our service log handler is attached after any external logging config
            try:
                root_logger = logging.getLogger()
                if not any(h.__class__.__name__ == 'ServiceLogHandler' for h in root_logger.handlers):
                    root_logger.addHandler(ServiceLogHandler())
                # set handler level to the configured level if available
                for h in root_logger.handlers:
                    if h.__class__.__name__ == 'ServiceLogHandler':
                        if hasattr(h, 'setLevel') and level is not None:
                            h.setLevel(level)
            except Exception:
                pass

            # Initialize components
            stability_checker = FileStabilityChecker(timeout=config.stable_wait_seconds)
            mover = LoggedPDFMover(Path(config.destination_root), dry_run=config.dry_run_mode)
            self.event_handler = PDFWatchHandler(mover, stability_checker)
            
            # Setup file watcher
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler, 
                config.workplace_path, 
                recursive=False
            )
            self.observer.start()
            
            self.status = "running"
            self.start_time = time.time()
            self.last_error = None
            
            await self.broadcast_status_update()
            
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            await self.broadcast_status_update()
            raise HTTPException(status_code=500, detail=str(e))
    
    async def stop_service(self):
        """Stop the file watching service."""
        if self.status == "stopped":
            return
            
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
                
            self.status = "stopped"
            self.start_time = None
            
            await self.broadcast_status_update()
            
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            await self.broadcast_status_update()
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_status(self) -> ServiceStatus:
        """Get current service status."""
        uptime = None
        if self.start_time and self.status == "running":
            uptime = int(time.time() - self.start_time)
            
        return ServiceStatus(
            status=self.status,
            uptime_seconds=uptime,
            files_processed_today=self.files_processed_today,
            queue_size=self.queue_size,
            last_error=self.last_error
        )
    
    async def broadcast_status_update(self):
        """Broadcast status update to all connected WebSocket clients."""
        if not self.websocket_connections:
            return
            
        status = self.get_status()
        message = {
            "type": "status_update",
            "data": status.dict()
        }
        
        # Remove disconnected websockets
        active_connections = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(message, default=str))
                active_connections.append(websocket)
            except:
                pass  # Connection closed
                
        self.websocket_connections = active_connections


# Global service manager instance
service_manager = ServiceManager()


# Logging handler that forwards Python logging records into the service manager
class ServiceLogHandler(logging.Handler):
    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.capacity = capacity

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created),
                level=record.levelname,
                message=record.getMessage(),
                module=record.module if hasattr(record, 'module') else '',
                file_path=getattr(record, 'pathname', None),
                extra_data=None
            )
            # Append entry (bounded capacity)
            service_manager.log_entries.append(entry)
            if len(service_manager.log_entries) > self.capacity:
                # trim oldest entries
                service_manager.log_entries.pop(0)
        except Exception:
            # Logging must not raise
            pass


# Install a single instance of the handler on the root logger if not present
_root_logger = logging.getLogger()
if not any(isinstance(h, ServiceLogHandler) for h in _root_logger.handlers):
    _root_logger.addHandler(ServiceLogHandler())


# Wrapper mover that records moves into service_manager for API-triggered operations
class LoggedPDFMover:
    def __init__(self, dest_root: Path, dry_run: bool = False):
        self.mover = PDFMover(dest_root, dry_run=dry_run)

    def move(self, source_path: Path, parsed_info: dict) -> bool:
        # Perform move and log result into service manager
        result = self.mover.move_signed_pdf(source_path, parsed_info)
        try:
            entry = LogEntry(
                timestamp=datetime.now(),
                level="INFO" if result else "ERROR",
                message=f"Moved {source_path} -> {parsed_info.get('client')}/{parsed_info.get('date')}/{parsed_info.get('status')}: {'OK' if result else 'FAIL'}",
                module=__name__,
                file_path=str(source_path),
                extra_data={"parsed": parsed_info}
            )
            service_manager.log_entries.append(entry)
            if len(service_manager.log_entries) > 1000:
                service_manager.log_entries.pop(0)

            # Update recent_files
            info = FileInfo(
                id=f"manual_{int(time.time())}",
                original_path=str(source_path),
                destination_path=None if self.mover.dry_run else None,
                status="processed" if result else "failed",
                detected_at=datetime.now(),
                processed_at=datetime.now() if result else None,
                file_size_bytes=source_path.stat().st_size if source_path.exists() else 0,
                error_message=None if result else "move failed",
                parsed_metadata=parsed_info
            )
            service_manager.recent_files.insert(0, info)
            if len(service_manager.recent_files) > 200:
                service_manager.recent_files.pop()
        except Exception:
            pass
        return result

    # Provide the same API as PDFMover used by the watcher
    def move_signed_pdf(self, source_path: Path, parsed_info: dict) -> bool:
        return self.move(source_path, parsed_info)


# Add a config persistence path (backend/config.json)
CONFIG_FILE = Path(__file__).resolve().parents[1] / "config.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: try to load persisted config
    if CONFIG_FILE.exists():
        try:
            raw = CONFIG_FILE.read_text()
            data = json.loads(raw)
            # Validate & set configuration (will raise on invalid paths)
            service_manager.configuration = Configuration(**data)
            logging.info(f"Loaded persisted configuration from {CONFIG_FILE}")
        except Exception as e:
            logging.warning(f"Failed to load persisted configuration: {e}")
    yield
    # Shutdown
    if service_manager.status == "running":
        await service_manager.stop_service()


# FastAPI app setup
app = FastAPI(
    title="File Organizer API",
    description="REST API for the Signed PDF File Organizer",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # UI dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Endpoints

@app.get("/api/v1/status", response_model=ServiceStatus)
async def get_service_status():
    """Get current service status."""
    return service_manager.get_status()


@app.api_route("/api/v1/start", methods=["GET", "POST"])
async def start_service_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    config: Optional[Configuration] = None
):
    """Start service on POST. Informational response on GET.
    If POST includes a Configuration JSON body, save and use it before starting.
    """
    if request.method == "GET":
        status = service_manager.get_status()
        return {
            "detail": "This endpoint requires POST to start the service. Use POST /api/v1/start.",
            "current_status": status.dict()
        }

    # POST: if config provided in body, persist and set it
    if config is not None:
        try:
            # Stop running service to apply new config safely
            if service_manager.status == "running":
                await service_manager.stop_service()

            # Assign and persist config as in /config endpoint
            service_manager.configuration = config
            try:
                CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
                CONFIG_FILE.write_text(json.dumps(config.dict(), indent=2))
                logging.info(f"Saved configuration to {CONFIG_FILE} via /start")
            except Exception as e:
                logging.error(f"Failed to persist configuration via /start: {e}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {e}")

    # Ensure configuration exists (either previously saved or provided now)
    if not service_manager.configuration:
        raise HTTPException(
            status_code=400,
            detail="Configuration required before starting service"
        )

    await service_manager.start_service(service_manager.configuration)
    return {"message": "Service started successfully"}


@app.api_route("/api/v1/stop", methods=["GET", "POST"])
async def stop_service_endpoint(request: Request):
    """Stop service on POST. Informational response on GET."""
    if request.method == "GET":
        status = service_manager.get_status()
        return {
            "detail": "This endpoint requires POST to stop the service. Use POST /api/v1/stop.",
            "current_status": status.dict()
        }

    # POST: perform stop
    await service_manager.stop_service()
    return {"message": "Service stopped successfully"}


@app.get("/api/v1/config", response_model=Configuration)
async def get_configuration():
    """Get current configuration."""
    if not service_manager.configuration:
        raise HTTPException(status_code=404, detail="No configuration found")
    return service_manager.configuration


@app.post("/api/v1/config")
async def update_configuration(config: Configuration):
    """Update configuration."""
    # Stop service if running
    if service_manager.status == "running":
        await service_manager.stop_service()
    
    service_manager.configuration = config

    # Persist configuration to disk
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(config.dict(), indent=2))
        logging.info(f"Saved configuration to {CONFIG_FILE}")
    except Exception as e:
        logging.error(f"Failed to persist configuration: {e}")

    return {"message": "Configuration updated successfully"}


@app.post("/api/v1/config/validate")
async def validate_configuration(config: Configuration):
    """Validate configuration without saving."""
    return {"message": "Configuration is valid", "config": config}


@app.get("/api/v1/files/recent", response_model=Dict[str, Any])
async def get_recent_files(
    limit: int = 50,
    status: Optional[str] = None,
    client: Optional[str] = None
):
    """Get recently processed files."""
    files = service_manager.recent_files
    
    # Apply filters
    if status:
        files = [f for f in files if f.status == status]
    if client:
        files = [f for f in files if f.parsed_metadata and 
                f.parsed_metadata.get('client', '').lower() == client.lower()]
    
    # Apply limit
    files = files[:limit]
    
    return {
        "files": files,
        "total": len(service_manager.recent_files),
        "has_more": len(service_manager.recent_files) > limit
    }


@app.get("/api/v1/files/preview")
async def preview_files():
    """Preview files that would be processed."""
    if not service_manager.configuration:
        raise HTTPException(status_code=400, detail="Configuration required")
    
    config = service_manager.configuration
    workplace_path = Path(config.workplace_path)
    
    preview_results = []
    total_files = 0
    would_process = 0
    would_skip = 0
    
    # Scan workplace directory
    for file_path in workplace_path.glob("*.pdf"):
        total_files += 1
        parsed = FilenameParser.parse_filename(file_path.name)
        
        # Check if parsed data contains a status that matches configured keywords
        if parsed and parsed.get('status') and any(
            keyword.lower() in parsed['status'].lower() 
            for keyword in config.status_keywords
        ):
            would_process += 1
            preview_results.append({
                "file_path": str(file_path),
                "would_process": True,
                "reason": "Matches pattern and contains signed status",
                "parsed_metadata": parsed
            })
        else:
            would_skip += 1
            preview_results.append({
                "file_path": str(file_path),
                "would_process": False,
                "reason": "No signed status keyword found" if parsed else "Filename doesn't match pattern",
                "parsed_metadata": parsed
            })
    
    return {
        "files": preview_results,
        "summary": {
            "total_files": total_files,
            "would_process": would_process,
            "would_skip": would_skip,
            "conflicts": 0  # TODO: Implement conflict detection
        }
    }


@app.post("/api/v1/files/reprocess")
async def reprocess_file(request: ProcessFileRequest):
    """Manually reprocess a specific file."""
    file_path = Path(request.file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not service_manager.configuration:
        raise HTTPException(status_code=400, detail="Configuration required")
    
    # If force=true, attempt immediate processing using the configured mover
    if request.force:
        try:
            config = service_manager.configuration
            mover = LoggedPDFMover(Path(config.destination_root), dry_run=config.dry_run_mode)

            parsed = FilenameParser.parse_filename(file_path.name)
            if not parsed:
                raise HTTPException(status_code=400, detail="Filename does not match expected pattern")

            if not FilenameParser.is_signed_status(parsed.get('status', '')):
                raise HTTPException(status_code=400, detail="File status not considered signed")

            success = mover.move(file_path, parsed)

            # Record recent file entry
            info = FileInfo(
                id=f"reproc_{int(time.time())}",
                original_path=str(file_path),
                destination_path=None if config.dry_run_mode else None,
                status="processed" if success else "failed",
                detected_at=datetime.now(),
                processed_at=datetime.now() if success else None,
                file_size_bytes=file_path.stat().st_size,
                error_message=None if success else "move failed",
                parsed_metadata=parsed
            )
            service_manager.recent_files.insert(0, info)
            # Keep recent_files bounded
            if len(service_manager.recent_files) > 200:
                service_manager.recent_files.pop()

            return {
                "message": "File reprocessed",
                "success": success,
                "processing_id": f"reproc_{int(time.time())}",
                "processed_at": datetime.now().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Default behavior: queued (not implemented)
    return {
        "message": "File queued for reprocessing",
        "processing_id": f"proc_{int(time.time())}",
        "estimated_completion": datetime.now().isoformat()
    }


@app.get("/api/v1/logs")
async def get_logs(
    level: Optional[str] = None,
    limit: int = 100,
    search: Optional[str] = None
):
    """Get application logs."""
    logs = service_manager.log_entries
    
    # Apply filters
    if level:
        logs = [log for log in logs if log.level == level.upper()]
    if search:
        logs = [log for log in logs if search.lower() in log.message.lower()]
    
    # Apply limit
    logs = logs[-limit:] if limit else logs
    
    return {
        "logs": logs,
        "total": len(service_manager.log_entries),
        "has_more": len(service_manager.log_entries) > limit
    }


@app.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    service_manager.websocket_connections.append(websocket)
    
    try:
        # Send initial status
        status = service_manager.get_status()
        await websocket.send_text(json.dumps({
            "type": "status_update",
            "data": status.dict()
        }, default=str))
        
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong, etc.)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in service_manager.websocket_connections:
            service_manager.websocket_connections.remove(websocket)


# Serve static files (UI) - only if built
ui_dist_path = Path("../ui/dist")
if ui_dist_path.exists():
    app.mount("/", StaticFiles(directory=str(ui_dist_path), html=True), name="static")


# single entrypoint
if __name__ == "__main__":
    logging.info("Starting File Organizer API on http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
