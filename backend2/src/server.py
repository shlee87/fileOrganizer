import time
from datetime import datetime, timezone
import logging
import re
import shutil
from pathlib import Path
from typing import Optional
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import queue
import os
import signal
import atexit

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
# Try using eventlet for better async handling, fallback to threading
try:
    import eventlet
    socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", async_mode='eventlet')
    print("Using eventlet async mode")
except ImportError:
    socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", async_mode='threading')
    print("Using threading async mode")

# --- In-Memory State Management ---
STATE = {
    "status": "stopped",  # running, stopped, error
    "start_time": None,
    "config": {
        "workplace_path": "/Users/seonghoonyi/Documents/projects/fileOrganizer/tests/fixtures/workplace",
        "destination_root": "/Users/seonghoonyi/Documents/projects/fileOrganizer/tests/fixtures/destination",
        "stability_wait_seconds": 10,
        "dry_run_mode": False,
        "status_keywords": ["signed"],
        "filename_pattern": r'^(?P<doc>.+?)_(?P<client>.+?)_(?P<date>\d{4}-?\d{2}-?\d{2})_(?P<status>.+?)\.pdf$',
        "log_level": "INFO",
    },
    "recent_files": [],
    "logs": [],
    "last_error": None,
    "files_processed_today": 0,
    "queue_size": 0,
    "observer_thread": None,
    "event_queue": queue.Queue(),
}

# Add thread safety lock
STATE_LOCK = threading.Lock()

# --- Core Logic from practice.py ---

class FilenameParser:
    """Parses PDF filenames according to the specified pattern."""

    @staticmethod
    def parse_filename(filename: str) -> Optional[dict]:
        pattern = re.compile(STATE["config"]["filename_pattern"], re.IGNORECASE)
        match = pattern.match(filename)
        if not match:
            return None
        return match.groupdict()

    @staticmethod
    def is_signed_status(status: str) -> bool:
        status_lower = status.lower()
        if '_signed' in status_lower:
            return True
        if 'unsigned' in status_lower:
            return False
        return any(indicator in status_lower for indicator in STATE["config"]["status_keywords"])

    @staticmethod
    def normalize_path_segment(segment: str) -> str:
        normalized = re.sub(r'[<>:"/\\|?*]', '', segment)
        normalized = re.sub(r'\s+', '_', normalized)
        return normalized.strip('_.')

class FileStabilityChecker:
    """Checks if a file has finished copying by monitoring size stability."""

    def __init__(self, timeout: float = 10.0, check_interval: float = 1.0):
        self.timeout = timeout
        self.check_interval = check_interval

    def wait_for_stability(self, filepath: Path) -> bool:
        if not filepath.exists():
            return False
        
        start_time = time.time()
        last_size = -1
        stable_count = 0
        effective_interval = min(self.check_interval, 0.5)
        required_stable = 1 if self.timeout >= 5.0 else 2
        mtime_grace = max(1.0, effective_interval * 2)

        while time.time() - start_time < self.timeout:
            try:
                stat = filepath.stat()
                current_size = stat.st_size
                mtime = stat.st_mtime
                size_stable = current_size == last_size and current_size > 0
                mtime_stable = current_size > 0 and (time.time() - mtime) >= mtime_grace

                if size_stable or mtime_stable:
                    stable_count += 1
                else:
                    stable_count = 0

                if stable_count >= required_stable:
                    return True

                last_size = current_size
                time.sleep(effective_interval)
            except (OSError, IOError):
                stable_count = 0
                time.sleep(effective_interval)
                continue

        return False

class PDFMover:
    """Handles moving PDFs to destination folders with duplicate handling."""

    def __init__(self, dest_root: Path, dry_run: bool = False):
        self.dest_root = Path(dest_root)
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)

    def move_signed_pdf(self, source_path: Path, parsed_info: dict) -> Optional[Path]:
        try:
            form_dir = FilenameParser.normalize_path_segment(parsed_info['doc'])
            client_dir = FilenameParser.normalize_path_segment(parsed_info['client'])
            date_dir = FilenameParser.normalize_path_segment(parsed_info['date'])
            status_dir = FilenameParser.normalize_path_segment(parsed_info['status'])
            
            dest_dir = self.dest_root / form_dir / client_dir / date_dir / status_dir
            dest_file = dest_dir / source_path.name
            
            if dest_file.exists():
                timestamp = int(time.time())
                stem = dest_file.stem
                suffix = dest_file.suffix
                dest_file = dest_dir / f"{stem}_{timestamp}{suffix}"
            
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would move: {source_path} -> {dest_file}")
                return dest_file
            
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_file))
            self.logger.info(f"Moved: {source_path} -> {dest_file}")
            return dest_file
            
        except Exception as e:
            self.logger.error(f"Failed to move {source_path}: {e}")
            return None

class MyHandler(FileSystemEventHandler):
    def __init__(self, event_queue: queue.Queue):
        self.event_queue = event_queue
        self.processing = set()
        self.processing_lock = threading.Lock()

    def _queue_event_if_pdf(self, event):
        if event.is_directory:
            return
        try:
            p = Path(event.src_path)
        except Exception:
            return
        # Only accept real .pdf files, ignore temp/partial/dotfiles
        if p.suffix.lower() != '.pdf':
            return
        if p.name.startswith('.') or p.name.endswith('.part') or p.name.endswith('~'):
            return

        if p in self.processing:
            return
        with self.processing_lock:
            if p in self.processing:
                return
            self.processing.add(p)
            self.event_queue.put(event)

        self.processing.add(p)
        self.event_queue.put(event)
        # update shared queue size and broadcast (with thread safety)
        with STATE_LOCK:
            STATE["queue_size"] = self.event_queue.qsize()
        try:
            socketio.emit('status_update', get_status_data())
        except Exception as e:
            logging.warning(f"Failed to emit status update: {e}")

    def on_created(self, event):
        self._queue_event_if_pdf(event)

    def on_modified(self, event):
        self._queue_event_if_pdf(event)

    def on_moved(self, event):
        if not event.is_directory:
            event.src_path = event.dest_path
            self._queue_event_if_pdf(event)

# --- Helper Functions ---

def add_log(level, message, file_path=None):
    """Helper to add a new log entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
        "module": "server",
        "file_path": file_path
    }
    with STATE_LOCK:
        STATE["logs"].insert(0, entry)
        if len(STATE["logs"]) > 1000:
            STATE["logs"].pop()
    
    logging.info(f"LOG [{level}]: {message}")
    try:
        socketio.emit('log_update', entry)
    except Exception as e:
        logging.warning(f"Failed to emit log update: {e}")

def broadcast_status():
    """Emits the current service status to all connected clients."""
    try:
        status_data = get_status_data()
        socketio.emit('status_update', status_data)
        logging.info(f"Broadcasted status update: {status_data['status']}")
    except Exception as e:
        logging.warning(f"Failed to broadcast status: {e}")

def get_status_data():
    """Constructs the status dictionary."""
    uptime = 0
    if STATE["status"] == "running" and STATE["start_time"]:
        uptime = int(time.time() - STATE["start_time"])
    
    return {
        "status": STATE["status"],
        "uptime_seconds": uptime,
        "files_processed_today": STATE["files_processed_today"],
        "queue_size": STATE["queue_size"],
        "last_error": STATE["last_error"],
    }

def file_processor_thread():
    config = STATE['config']
    stability_checker = FileStabilityChecker(timeout=config['stability_wait_seconds'])
    mover = PDFMover(Path(config['destination_root']), dry_run=config['dry_run_mode'])
    
    while STATE['status'] == 'running':
        try:
            event = STATE['event_queue'].get(timeout=1)
            # update queue size after removing item (with thread safety)
            with STATE_LOCK:
                STATE["queue_size"] = STATE['event_queue'].qsize()
            
            filepath = Path(event.src_path)
            
            try:
                if filepath.suffix.lower() != '.pdf':
                    continue

                add_log("INFO", f"Processing file: {filepath}", file_path=str(filepath))
                
                try:
                    stat_info = filepath.stat()
                except FileNotFoundError:
                    add_log("WARNING", f"File not found: {filepath}", file_path=str(filepath))
                    continue

                parsed_info = FilenameParser.parse_filename(filepath.name)
                if not parsed_info:
                    add_log("INFO", f"Filename doesn't match pattern: {filepath.name}", file_path=str(filepath))
                    continue
                
                if not FilenameParser.is_signed_status(parsed_info['status']):
                    add_log("INFO", f"Document not signed, ignoring: {filepath.name}", file_path=str(filepath))
                    continue
                
                add_log("INFO", f"Found signed document: {filepath.name}", file_path=str(filepath))
                
                if not stability_checker.wait_for_stability(filepath):
                    add_log("WARNING", f"File did not stabilize within timeout: {filepath}", file_path=str(filepath))
                    continue
                
                destination_path = mover.move_signed_pdf(filepath, parsed_info)
                
                status = "processed" if destination_path else "failed"
                error_message = None if destination_path else "Failed to move file"

                file_info = {
                    "id": str(filepath.name),
                    "original_path": str(filepath),
                    "destination_path": str(destination_path) if destination_path else None,
                    "status": status,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "detected_at": datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc).isoformat(),
                    "file_size_bytes": stat_info.st_size,
                    "error_message": error_message,
                    "parsed_metadata": parsed_info
                }
                with STATE_LOCK:
                    STATE["recent_files"].insert(0, file_info)
                    if len(STATE["recent_files"]) > 100:
                        STATE["recent_files"].pop()
                
                try:
                    socketio.emit('file.processed', file_info)
                except Exception as e:
                    logging.warning(f"Failed to emit file processed event: {e}")
                
                if destination_path:
                    with STATE_LOCK:
                        STATE["files_processed_today"] += 1
                    broadcast_status()
            finally:
                handler = STATE.get('event_handler')
                if handler and isinstance(handler, MyHandler):
                    if filepath in handler.processing:
                        handler.processing.remove(filepath)
                    with handler.processing_lock:
                        if filepath in handler.processing:
                            handler.processing.remove(filepath)
        except queue.Empty:
            continue
        except Exception as e:
            add_log("ERROR", f"Error in file processor thread: {e}")
            time.sleep(1)  # Prevent tight error loops

# --- API Endpoints ---

@app.route('/api/v1/status', methods=['GET'])
def get_status():
    return jsonify(get_status_data())

@app.route('/api/v1/start-simple', methods=['POST'])
def start_service_simple():
    """Simplified start service without observer for testing."""
    try:
        add_log("INFO", "Simple start command received")
        
        with STATE_LOCK:
            if STATE["status"] == "running":
                return jsonify({"error": "Service is already running"}), 409
            
            STATE["status"] = "running" 
            STATE["start_time"] = time.time()
            STATE["last_error"] = None
        
        add_log("INFO", "Simple start completed successfully")
        return jsonify({"message": "Simple start successful", "status": "running"})
        
    except Exception as e:
        error_msg = f"Simple start failed: {str(e)}"
        add_log("ERROR", error_msg)
        return jsonify({"error": error_msg}), 500

@app.route('/api/v1/start', methods=['POST'])
def start_service():
    try:
        add_log("INFO", "Full start command received. Starting service...")
        
        with STATE_LOCK:
            if STATE["status"] == "running":
                return jsonify({"error": "Service is already running"}), 409

            STATE["status"] = "running"
            STATE["start_time"] = time.time()
            STATE["last_error"] = None

        add_log("INFO", "Preparing workplace directory...")
        workplace = Path(STATE["config"]['workplace_path'])
        try:
            workplace.mkdir(parents=True, exist_ok=True)
            add_log("INFO", f"Workplace directory ready: {workplace}")
        except Exception as e:
            add_log("ERROR", f"Failed to create workplace directory: {e}", file_path=str(workplace))
            with STATE_LOCK:
                STATE["status"] = "error"
                STATE["last_error"] = str(e)
            return jsonify({"error": "Failed to prepare workplace path"}), 500

        add_log("INFO", "Preparing destination directory...")
        dest_path = Path(STATE["config"]['destination_root'])
        try:
            dest_path.mkdir(parents=True, exist_ok=True)
            add_log("INFO", f"Destination directory ready: {dest_path}")
        except Exception as e:
            add_log("ERROR", f"Failed to create destination directory: {e}", file_path=str(dest_path))
            with STATE_LOCK:
                STATE["status"] = "error"
                STATE["last_error"] = str(e)
            return jsonify({"error": "Failed to prepare destination path"}), 500

        add_log("INFO", "Creating filesystem observer...")
        event_handler = MyHandler(STATE['event_queue'])
        STATE['event_handler'] = event_handler
        observer = Observer()
        
        add_log("INFO", "Starting filesystem observer...")
        try:
            observer.schedule(event_handler, str(workplace), recursive=False)
            observer.start()
            add_log("INFO", f"Filesystem observer started for: {workplace}")
        except Exception as e:
            add_log("ERROR", f"Failed to start filesystem observer: {e}")
            with STATE_LOCK:
                STATE["status"] = "error"
                STATE["last_error"] = str(e)
            return jsonify({"error": f"Failed to start observer: {str(e)}"}), 500

        STATE['observer'] = observer

        add_log("INFO", "Starting background file processor...")
        try:
            # Use threading.Thread instead of socketio.start_background_task to avoid potential blocking
            bg_thread = threading.Thread(target=file_processor_thread, daemon=True)
            bg_thread.start()
            STATE['observer_thread'] = bg_thread
            add_log("INFO", "Background file processor started successfully")
        except Exception as e:
            add_log("ERROR", f"Failed to start background task: {e}")
            try:
                observer.stop()
                observer.join(timeout=2)
            except Exception:
                pass
            with STATE_LOCK:
                STATE["status"] = "error"
                STATE["last_error"] = str(e)
            return jsonify({"error": f"Failed to start background processor: {str(e)}"}), 500
        
        add_log("INFO", "Broadcasting initial status...")
        try:
            broadcast_status()
        except Exception as e:
            add_log("WARNING", f"Failed to broadcast initial status: {e}")
        
        add_log("INFO", "Service started successfully!")
        return jsonify({
            "message": "Service started successfully",
            "workplace_path": str(workplace),
            "destination_path": str(dest_path),
            "status": "running"
        })
        
    except Exception as e:
        error_msg = f"Unexpected error during service start: {str(e)}"
        add_log("ERROR", error_msg)
        with STATE_LOCK:
            STATE["status"] = "error"
            STATE["last_error"] = error_msg
        return jsonify({"error": error_msg}), 500

@app.route('/api/v1/stop', methods=['POST'])
def stop_service():
    try:
        with STATE_LOCK:
            if STATE["status"] == "stopped":
                return jsonify({"error": "Service is already stopped"}), 409
            
            add_log("INFO", "Stop command received")
            STATE["status"] = "stopped"
            STATE["start_time"] = None

        # Stop and wait for observer and processor threads to finish
        observer = STATE.get('observer')
        processor_thread = STATE.get('observer_thread')

        if observer:
            add_log("INFO", "Stopping file system observer...")
            observer.stop()
            observer.join(timeout=5) # Wait for observer to terminate
        
        if processor_thread and processor_thread.is_alive():
            add_log("INFO", "Waiting for file processor to finish...")
            processor_thread.join(timeout=5) # Wait for processor to terminate

        STATE['observer'] = None
        STATE['observer_thread'] = None
        
        add_log("INFO", "Service stopped successfully")
        broadcast_status()
        return jsonify({"message": "Service stopped successfully"})
        
    except Exception as e:
        error_msg = f"Failed to stop gracefully: {str(e)}"
        add_log("ERROR", error_msg)
        with STATE_LOCK:
            STATE["status"] = "error"
            STATE["last_error"] = error_msg
        broadcast_status()
        return jsonify({"error": error_msg}), 500

@app.route('/api/v1/force-reset', methods=['POST'])
def force_reset():
    """Force reset the service state without cleanup."""
    try:
        with STATE_LOCK:
            STATE["status"] = "stopped"
            STATE["start_time"] = None
            STATE["last_error"] = None
            STATE["files_processed_today"] = 0
            STATE["queue_size"] = 0
        
        STATE['observer'] = None
        STATE['observer_thread'] = None
        
        # Clear the event queue
        while not STATE['event_queue'].empty():
            try:
                STATE['event_queue'].get_nowait()
            except:
                break
        
        add_log("INFO", "Service state force reset")
        return jsonify({"message": "Service state reset successfully"})
        
    except Exception as e:
        add_log("ERROR", f"Force reset error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        new_config = request.json
        if not new_config:
            return jsonify({"error": "Invalid configuration data"}), 400
        
        STATE["config"].update(new_config)
        add_log("INFO", "Configuration updated.")
        return jsonify({"message": "Configuration updated successfully", "restart_required": True})
    else: # GET
        return jsonify(STATE["config"])

@app.route('/api/v1/files/recent', methods=['GET'])
def get_recent_files():
    return jsonify({"files": STATE["recent_files"], "total": len(STATE["recent_files"])
, "has_more": False})

@app.route('/api/v1/files/preview', methods=['GET'])
def get_file_preview():
    config = STATE['config']
    workplace_path = Path(config['workplace_path'])
    preview_results = []
    total_files = 0
    would_process = 0
    would_skip = 0

    if workplace_path.exists() and workplace_path.is_dir():
        for file_path in workplace_path.iterdir():
            if not file_path.is_file():
                continue

            total_files += 1

            if file_path.suffix.lower() == '.pdf':
                parsed = FilenameParser.parse_filename(file_path.name)
                
                if parsed and FilenameParser.is_signed_status(parsed.get('status', '')):
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
            else:
                would_skip += 1
                preview_results.append({
                    "file_path": str(file_path),
                    "would_process": False,
                    "reason": "Non-PDF file, skipped",
                    "parsed_metadata": None
                })

    return jsonify({
        "files": preview_results,
        "summary": {
            "total_files": total_files,
            "would_process": would_process,
            "would_skip": would_skip,
            "conflicts": 0
        }
    })

@app.route('/api/v1/logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": STATE["logs"], "total": len(STATE["logs"])
, "has_more": False})

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service_status": STATE["status"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check server state."""
    return jsonify({
        "status": "debug_ok",
        "state_status": STATE["status"],
        "observer_running": STATE.get('observer') is not None,
        "thread_running": STATE.get('observer_thread') is not None,
        "queue_size": STATE["queue_size"],
        "logs_count": len(STATE["logs"])
    })

@app.route('/api/v1/test/rename', methods=['POST'])
def test_file_rename():
    """Test endpoint to verify file rename detection and processing."""
    try:
        data = request.get_json()
        if not data or 'original_name' not in data or 'new_name' not in data:
            return jsonify({"error": "Missing original_name or new_name in request body"}), 400
        
        workplace = Path(STATE["config"]['workplace_path'])
        original_file = workplace / data['original_name']
        new_file = workplace / data['new_name']
        
        # Create test file if it doesn't exist
        if not original_file.exists():
            workplace.mkdir(parents=True, exist_ok=True)
            original_file.write_text("Test PDF content - created for testing file organization")
            add_log("INFO", f"Created test file: {original_file}")
        
        # Rename the file
        original_file.rename(new_file)
        add_log("INFO", f"Renamed {original_file.name} to {new_file.name}")
        
        # Check if new filename would be processed
        parsed = FilenameParser.parse_filename(new_file.name)
        would_process = False
        if parsed:
            would_process = FilenameParser.is_signed_status(parsed.get('status', ''))
        
        reason = "Matches pattern and signed status" if would_process else (
                "No signed status keyword" if parsed else "Doesn't match filename pattern")
        
        return jsonify({
            "success": True,
            "message": f"File renamed from {data['original_name']} to {data['new_name']}",
            "file_path": str(new_file),
            "parsed_metadata": parsed,
            "would_process": would_process,
            "reason": reason,
            "service_running": STATE["status"] == "running"
        })
        
    except Exception as e:
        error_msg = f"Test rename failed: {str(e)}"
        add_log("ERROR", error_msg)
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/api/v1/test/create-sample', methods=['POST'])
def create_sample_files():
    """Create sample files for testing."""
    try:
        data = request.get_json() or {}
        force_recreate = data.get('force', False)
        
        workplace = Path(STATE["config"]['workplace_path'])
        workplace.mkdir(parents=True, exist_ok=True)
        
        sample_files = [
            "Contract_ClientA_2024-01-15_signed.pdf",
            "Invoice_ClientB_2024-01-16_executed.pdf", 
            "Agreement_ClientC_2024-01-17_unsigned.pdf",
            "random_file.pdf"
        ]
        
        created_files = []
        existing_files = []
        
        for filename in sample_files:
            file_path = workplace / filename
            if file_path.exists():
                existing_files.append(filename)
                if force_recreate:
                    file_path.write_text(f"Sample content for {filename} - recreated at {datetime.now()}")
                    created_files.append(f"{filename} (recreated)")
            else:
                file_path.write_text(f"Sample content for {filename} - created at {datetime.now()}")
                created_files.append(filename)
        
        message = f"Created {len(created_files)} sample files"
        if existing_files:
            message += f", found {len(existing_files)} existing files"
        
        add_log("INFO", message)
        
        return jsonify({
            "success": True,
            "message": message,
            "created_files": created_files,
            "existing_files": existing_files,
            "workplace_path": str(workplace),
            "total_files": len(list(workplace.glob("*.pdf")))
        })
        
    except Exception as e:
        error_msg = f"Failed to create sample files: {str(e)}"
        add_log("ERROR", error_msg)
        return jsonify({"success": False, "error": error_msg}), 500

# --- WebSocket Events ---

@socketio.on('connect')
def handle_connect():
    logging.info("Client connected to WebSocket")
    emit('status_update', get_status_data())

@socketio.on('disconnect')
def handle_disconnect():
    logging.info("Client disconnected")


# --- Cleanup and Signal Handling ---

def cleanup_on_exit():
    """Clean up resources when the application exits."""
    if STATE.get("status") == "running":
        add_log("INFO", "Application shutting down, stopping service...")
        observer = STATE.get('observer')
        if observer:
            try:
                observer.stop()
                observer.join(timeout=3)
            except Exception as e:
                logging.error(f"Error during cleanup: {e}")

# Register cleanup function
atexit.register(cleanup_on_exit)

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown."""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    cleanup_on_exit()
    # Use sys.exit() instead of os._exit() to allow proper cleanup
    import sys
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Add a simple keyboard interrupt handler for socketio
def keyboard_interrupt_handler():
    """Handle keyboard interrupt during socketio.run()"""
    try:
        socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, shutting down...")
        cleanup_on_exit()
        import sys
        sys.exit(0)

# --- Main Execution ---

if __name__ == '__main__':
    add_log("INFO", "Flask server starting up.")
    print("Starting File Organizer Server on http://0.0.0.0:8080")
    print("Press Ctrl+C to stop the server")
    
    try:
        keyboard_interrupt_handler()
    except Exception as e:
        add_log("ERROR", f"Failed to start server: {e}")
        print(f"Server startup failed: {e}")
        raise
    finally:
        print("Server shutdown complete.")