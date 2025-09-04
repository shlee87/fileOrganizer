import time
import logging
import re
import shutil
from pathlib import Path
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- In-Memory State Management ---
STATE = {
    "config": {
        "workplace_path": "/Users/seonghoonyi/Documents/projects/fileOrganizer/tests/fixtures/workplace",
        "destination_root": "/Users/seonghoonyi/Documents/projects/fileOrganizer/tests/fixtures/destination",
        "stability_wait_seconds": 10,
        "dry_run_mode": False,
        "status_keywords": ["signed", "executed", "final"],
        "filename_pattern": r'^(?P<doc>.+?)_(?P<client>.+?)_(?P<date>\d{4}-?\d{2}-?\d{2})_(?P<status>.+?)\.pdf$',
    },
}

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
    def __init__(self, mover: PDFMover, stability_checker: FileStabilityChecker):
        self.mover = mover
        self.stability_checker = stability_checker
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        if not event.is_directory:
            self._process_file(Path(event.src_path))

    def _process_file(self, filepath: Path):
        if filepath.suffix.lower() != '.pdf':
            return
        
        logging.info(f"Processing file: {filepath}")
        
        parsed_info = FilenameParser.parse_filename(filepath.name)
        if not parsed_info:
            logging.info(f"Filename doesn't match pattern: {filepath.name}")
            return
        
        if not FilenameParser.is_signed_status(parsed_info['status']):
            logging.info(f"Document not signed, ignoring: {filepath.name}")
            return
        
        logging.info(f"Found signed document: {filepath.name}")
        
        if not self.stability_checker.wait_for_stability(filepath):
            logging.warning(f"File did not stabilize within timeout: {filepath}")
            return
        
        self.mover.move_signed_pdf(filepath, parsed_info)

if __name__ == "__main__":
    config = STATE['config']
    stability_checker = FileStabilityChecker(timeout=config['stability_wait_seconds'])
    mover = PDFMover(Path(config['destination_root']), dry_run=config['dry_run_mode'])
    event_handler = MyHandler(mover, stability_checker)
    
    observer = Observer()
    observer.schedule(event_handler, config['workplace_path'], recursive=False)
    observer.start()
    print(f'Watching directory: {config["workplace_path"]}')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()