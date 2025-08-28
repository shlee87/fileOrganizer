#!/usr/bin/env python3
"""
Test script to process existing files in workplace folder (one-time scan).
"""

import sys
from pathlib import Path
sys.path.append('.')

from signed_watcher import FilenameParser, PDFMover, FileStabilityChecker
import logging

def test_existing_files(workplace_path, dest_path, dry_run=True):
    """Process all existing PDF files in workplace folder."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    workplace = Path(workplace_path)
    
    # Initialize components
    mover = PDFMover(dest_path, dry_run=dry_run)
    stability_checker = FileStabilityChecker(timeout=0.5, check_interval=0.1)  # Very short for existing files
    
    logger.info(f"Scanning workplace: {workplace}")
    logger.info(f"Destination: {dest_path}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("-" * 50)
    
    # Process all PDF files
    pdf_files = list(workplace.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    for pdf_file in pdf_files:
        logger.info(f"Processing: {pdf_file.name}")
        
        # Parse filename
        parsed_info = FilenameParser.parse_filename(pdf_file.name)
        if not parsed_info:
            logger.info(f"  ❌ Invalid pattern: {pdf_file.name}")
            continue
            
        # Check if signed
        if not FilenameParser.is_signed_status(parsed_info['status']):
            logger.info(f"  ❌ Not signed (status: {parsed_info['status']})")
            continue
            
        logger.info(f"  ✅ Signed document found!")
        logger.info(f"     Form: {parsed_info['doc']}")
        logger.info(f"     Client: {parsed_info['client']}")
        logger.info(f"     Date: {parsed_info['date']}")
        logger.info(f"     Status: {parsed_info['status']}")
        
        # Wait for stability (should be immediate for existing files)
        if stability_checker.wait_for_stability(pdf_file):
            # Move the file
            mover.move_signed_pdf(pdf_file, parsed_info)
        else:
            logger.warning(f"  ⚠️  File not stable: {pdf_file.name}")
            
        logger.info("")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python test_existing_files.py <workplace_path> <dest_path>")
        sys.exit(1)
        
    test_existing_files(sys.argv[1], sys.argv[2], dry_run=True)