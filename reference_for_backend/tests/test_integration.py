#!/usr/bin/env python3
"""
Integration tests for signed_watcher module.
Tests the full workflow end-to-end.
"""

import unittest
import tempfile
import os
import shutil
import time
from pathlib import Path
import sys

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from signed_watcher import PDFMover, FileStabilityChecker


class TestPDFWorkflowIntegration(unittest.TestCase):
    """Integration tests for the complete PDF processing workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.workplace = Path(self.temp_dir) / 'workplace'
        self.destination = Path(self.temp_dir) / 'destination'
        self.workplace.mkdir()
        self.destination.mkdir()
        
        # Create real components
        self.mover = PDFMover(self.destination)
        self.stability_checker = FileStabilityChecker(timeout=1.0, check_interval=0.1)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_pdf_processing_workflow(self):
        """Test the complete workflow from file creation to organized storage."""
        # Create a test PDF file with correct naming
        test_filename = 'contract_TestClient_2024-01-15_signed.pdf'
        test_file = self.workplace / test_filename
        
        # Write test content
        test_file.write_text('Mock PDF content for testing')
        
        # Wait for file to be stable
        is_stable = self.stability_checker.wait_for_stability(test_file)
        self.assertTrue(is_stable, "File should be stable")
        
        # Parse the filename (simulating the parser)
        parsed_info = {
            'doc': 'contract',
            'client': 'TestClient',
            'date': '2024-01-15',
            'status': 'signed'
        }
        
        # Move the file
        success = self.mover.move_signed_pdf(test_file, parsed_info)
        self.assertTrue(success, "PDF move should succeed")
        
        # Verify the file was moved to the correct location
        expected_path = (self.destination / 'contract' / 'TestClient' / 
                        '2024-01-15' / 'signed' / test_filename)
        
        self.assertTrue(expected_path.exists(), f"File should exist at {expected_path}")
        self.assertFalse(test_file.exists(), "Original file should be moved")
        
        # Verify content is preserved
        moved_content = expected_path.read_text()
        self.assertEqual(moved_content, 'Mock PDF content for testing')
    
    def test_duplicate_file_handling(self):
        """Test handling of duplicate files with timestamp suffix."""
        test_filename = 'NDA_ClientCorp_20240815_executed.pdf'
        
        # Create the first file
        test_file1 = self.workplace / test_filename
        test_file1.write_text('First file content')
        
        parsed_info = {
            'doc': 'NDA',
            'client': 'ClientCorp',
            'date': '20240815',
            'status': 'executed'
        }
        
        # Move first file
        success1 = self.mover.move_signed_pdf(test_file1, parsed_info)
        self.assertTrue(success1)
        
        # Create second file with same name
        test_file2 = self.workplace / test_filename
        test_file2.write_text('Second file content')
        
        # Move second file - should get timestamp suffix
        success2 = self.mover.move_signed_pdf(test_file2, parsed_info)
        self.assertTrue(success2)
        
        # Verify both files exist in destination
        dest_dir = self.destination / 'NDA' / 'ClientCorp' / '20240815' / 'executed'
        files_in_dest = list(dest_dir.glob('*.pdf'))
        
        self.assertEqual(len(files_in_dest), 2, "Should have 2 files in destination")
        
        # One should be original name, one should have timestamp
        filenames = [f.name for f in files_in_dest]
        self.assertIn(test_filename, filenames, "Original filename should exist")
        
        # Check that one file has timestamp suffix
        timestamped_files = [f for f in filenames if f != test_filename]
        self.assertEqual(len(timestamped_files), 1, "Should have one timestamped file")
        self.assertTrue(timestamped_files[0].startswith('NDA_ClientCorp_20240815_executed_'))
    
    def test_dry_run_workflow(self):
        """Test the complete workflow in dry-run mode."""
        # Create mover in dry-run mode
        dry_run_mover = PDFMover(self.destination, dry_run=True)
        
        test_filename = 'service_StartupBeta_2024-07-30_final.pdf'
        test_file = self.workplace / test_filename
        test_file.write_text('Test content')
        
        parsed_info = {
            'doc': 'service',
            'client': 'StartupBeta',
            'date': '2024-07-30',
            'status': 'final'
        }
        
        # Process in dry-run mode
        success = dry_run_mover.move_signed_pdf(test_file, parsed_info)
        self.assertTrue(success, "Dry run should report success")
        
        # Verify original file still exists
        self.assertTrue(test_file.exists(), "Original file should remain in dry-run mode")
        
        # Verify no files were created in destination
        expected_path = (self.destination / 'service' / 'StartupBeta' / 
                        '2024-07-30' / 'final' / test_filename)
        self.assertFalse(expected_path.exists(), "No file should be created in dry-run mode")


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests
    unittest.main()
