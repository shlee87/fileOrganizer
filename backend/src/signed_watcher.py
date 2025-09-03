#!/usr/bin/env python3
"""
Signed PDF File Organizer
Watches a workplace folder and automatically moves signed PDFs to organized destination folders.
"""

import argparse
import logging
import os
import re
import shutil
import time
from pathlib import Path
from typing import Optional, Tuple
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FilenameParser:
    """Parses PDF filenames according to the specified pattern."""
    
    FILENAME_PATTERN = re.compile(
        r'^(?P<doc>.+?)_(?P<client>.+?)_(?P<date>\d{4}-?\d{2}-?\d{2})_(?P<status>.+?)\.pdf$',
        re.IGNORECASE
    )
    
    SIGNED_INDICATORS = ['signed', 'executed', 'final']
    
    @classmethod
    def parse_filename(cls, filename: str) -> Optional[dict]:
        """
        Parse filename and return components if it matches the pattern.
        
        Args:
            filename: The filename to parse
            
        Returns:
            Dict with doc, client, date, status if valid, None otherwise
        """
        match = cls.FILENAME_PATTERN.match(filename)
        if not match:
            return None
        return match.groupdict()
    
    @classmethod
    def is_signed_status(cls, status: str) -> bool:
        """
        Check if status indicates a signed document.
        
        Args:
            status: The status string from filename
            
        Returns:
            True if status indicates signed document
        """
        status_lower = status.lower()
        
        # Check for explicit _signed tag
        if '_signed' in status_lower:
            return True
            
        # Check for signed indicators, but exclude "unsigned"
        if 'unsigned' in status_lower:
            return False
            
        return any(indicator in status_lower for indicator in cls.SIGNED_INDICATORS)
    
    @staticmethod
    def normalize_path_segment(segment: str) -> str:
        """
        Normalize a path segment by replacing unsafe characters.
        
        Args:
            segment: The path segment to normalize
            
        Returns:
            Normalized path segment
        """
        # Replace spaces with underscores and remove/replace unsafe characters
        normalized = re.sub(r'[<>:"/\\|?*]', '', segment)
        normalized = re.sub(r'\s+', '_', normalized)
        return normalized.strip('_.')


class FileStabilityChecker:
    """Checks if a file has finished copying by monitoring size stability."""
    
    def __init__(self, timeout: float = 10.0, check_interval: float = 1.0):
        self.timeout = timeout
        self.check_interval = check_interval
    
    def wait_for_stability(self, filepath: Path) -> bool:
        """
        Wait for file size to stabilize, indicating copy completion.
        
        Args:
            filepath: Path to the file to monitor
            
        Returns:
            True if file is stable, False if timeout reached
        """
        if not filepath.exists():
            return False
        
        start_time = time.time()
        last_size = -1
        stable_count = 0
        
        while time.time() - start_time < self.timeout:
            try:
                current_size = filepath.stat().st_size
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= 2:  # Require 2 consecutive stable checks
                        return True
                else:
                    stable_count = 0
                last_size = current_size
                time.sleep(self.check_interval)
            except (OSError, IOError):
                # File might be temporarily inaccessible during copy
                time.sleep(self.check_interval)
                continue
        
        return False


class PDFMover:
    """Handles moving PDFs to destination folders with duplicate handling."""
    
    def __init__(self, dest_root: Path, dry_run: bool = False):
        self.dest_root = Path(dest_root)
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
    
    def move_signed_pdf(self, source_path: Path, parsed_info: dict) -> bool:
        """
        Move a signed PDF to the appropriate destination folder.
        
        Args:
            source_path: Source file path
            parsed_info: Parsed filename information
            
        Returns:
            True if move was successful (or would be in dry-run mode)
        """
        try:
            # Create destination path: form/client/date/status
            form_dir = FilenameParser.normalize_path_segment(parsed_info['doc'])
            client_dir = FilenameParser.normalize_path_segment(parsed_info['client'])
            date_dir = FilenameParser.normalize_path_segment(parsed_info['date'])
            status_dir = FilenameParser.normalize_path_segment(parsed_info['status'])
            
            dest_dir = self.dest_root / form_dir / client_dir / date_dir / status_dir
            dest_file = dest_dir / source_path.name
            
            # Handle duplicate filenames
            if dest_file.exists():
                timestamp = int(time.time())
                stem = dest_file.stem
                suffix = dest_file.suffix
                dest_file = dest_dir / f"{stem}_{timestamp}{suffix}"
            
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would move: {source_path} -> {dest_file}")
                return True
            
            # Create destination directory if it doesn't exist
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source_path), str(dest_file))
            self.logger.info(f"Moved: {source_path} -> {dest_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move {source_path}: {e}")
            return False


class PDFWatchHandler(FileSystemEventHandler):
    """Handles filesystem events for PDF files in the workplace folder."""
    
    def __init__(self, mover: PDFMover, stability_checker: FileStabilityChecker):
        self.mover = mover
        self.stability_checker = stability_checker
        self.logger = logging.getLogger(__name__)
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self._process_file(Path(event.src_path))
    
    def on_moved(self, event):
        """Handle file rename/move events."""
        if not event.is_directory:
            self._process_file(Path(event.dest_path))
    
    def _process_file(self, filepath: Path):
        """Process a potentially new PDF file."""
        # Only process PDF files
        if filepath.suffix.lower() != '.pdf':
            return
        
        self.logger.info(f"Processing file: {filepath}")
        
        # Parse filename
        parsed_info = FilenameParser.parse_filename(filepath.name)
        if not parsed_info:
            self.logger.info(f"Filename doesn't match pattern: {filepath.name}")
            return
        
        # Check if it's a signed document
        if not FilenameParser.is_signed_status(parsed_info['status']):
            self.logger.info(f"Document not signed, ignoring: {filepath.name}")
            return
        
        self.logger.info(f"Found signed document: {filepath.name}")
        
        # Wait for file stability
        if not self.stability_checker.wait_for_stability(filepath):
            self.logger.warning(f"File did not stabilize within timeout: {filepath}")
            return
        
        # Move the file
        self.mover.move_signed_pdf(filepath, parsed_info)


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Watch for signed PDFs and organize them automatically'
    )
    parser.add_argument(
        'workplace',
        help='Path to the workplace folder to watch'
    )
    parser.add_argument(
        'dest_root',
        help='Root path for organized destination folders'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Log actions without actually moving files'
    )
    parser.add_argument(
        '--stability-timeout',
        type=float,
        default=10.0,
        help='Seconds to wait for file size to stabilize (default: 10.0)'
    )
    parser.add_argument(
        '--log-file',
        help='Path to log file (logs to console if not specified)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_file)
    
    # Validate paths
    workplace_path = Path(args.workplace)
    if not workplace_path.exists() or not workplace_path.is_dir():
        logger.error(f"Workplace path does not exist or is not a directory: {workplace_path}")
        return 1
    
    dest_root_path = Path(args.dest_root)
    
    logger.info(f"Starting PDF watcher")
    logger.info(f"Workplace: {workplace_path}")
    logger.info(f"Destination root: {dest_root_path}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Stability timeout: {args.stability_timeout}s")
    
    # Initialize components
    stability_checker = FileStabilityChecker(timeout=args.stability_timeout)
    mover = PDFMover(dest_root_path, dry_run=args.dry_run)
    event_handler = PDFWatchHandler(mover, stability_checker)
    
    # Setup file watcher
    observer = Observer()
    observer.schedule(event_handler, str(workplace_path), recursive=False)
    observer.start()
    
    try:
        logger.info("Watching for changes... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
        observer.stop()
    
    observer.join()
    logger.info("PDF watcher stopped")
    return 0


if __name__ == '__main__':
    exit(main())