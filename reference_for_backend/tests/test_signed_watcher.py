#!/usr/bin/env python3
"""
Unit tests for signed_watcher module.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from signed_watcher import FilenameParser, PDFMover, PDFWatchHandler, FileStabilityChecker


class TestFilenameParser(unittest.TestCase):
    """Test cases for FilenameParser class."""
    
    def test_parse_valid_filename_with_dashes(self):
        """Test parsing a valid filename with dashes in date."""
        filename = "contract_StartupAlpha_2024-08-21_signed.pdf"
        result = FilenameParser.parse_filename(filename)
        
        expected = {
            'doc': 'contract',
            'client': 'StartupAlpha', 
            'date': '2024-08-21',
            'status': 'signed'
        }
        self.assertEqual(result, expected)
    
    def test_parse_valid_filename_without_dashes(self):
        """Test parsing a valid filename without dashes in date."""
        filename = "NDA_TechCorp_20240815_executed.pdf"
        result = FilenameParser.parse_filename(filename)
        
        expected = {
            'doc': 'NDA',
            'client': 'TechCorp',
            'date': '20240815', 
            'status': 'executed'
        }
        self.assertEqual(result, expected)
    
    def test_parse_invalid_filename(self):
        """Test parsing an invalid filename."""
        filename = "invalid_filename.pdf"
        result = FilenameParser.parse_filename(filename)
        self.assertIsNone(result)
    
    def test_parse_non_pdf_file(self):
        """Test parsing a non-PDF file."""
        filename = "not_a_pdf.txt"
        result = FilenameParser.parse_filename(filename)
        self.assertIsNone(result)
    
    def test_is_signed_status_signed(self):
        """Test signed status detection for 'signed'."""
        self.assertTrue(FilenameParser.is_signed_status('signed'))
        self.assertTrue(FilenameParser.is_signed_status('SIGNED'))
    
    def test_is_signed_status_executed(self):
        """Test signed status detection for 'executed'."""
        self.assertTrue(FilenameParser.is_signed_status('executed'))
        self.assertTrue(FilenameParser.is_signed_status('EXECUTED'))
    
    def test_is_signed_status_final(self):
        """Test signed status detection for 'final'."""
        self.assertTrue(FilenameParser.is_signed_status('final'))
        self.assertTrue(FilenameParser.is_signed_status('FINAL'))
    
    def test_is_signed_status_with_underscore(self):
        """Test signed status detection with underscore."""
        self.assertTrue(FilenameParser.is_signed_status('fully_signed'))
        self.assertTrue(FilenameParser.is_signed_status('contract_signed'))
    
    def test_is_signed_status_not_signed(self):
        """Test signed status detection for non-signed statuses."""
        self.assertFalse(FilenameParser.is_signed_status('draft'))
        self.assertFalse(FilenameParser.is_signed_status('pending'))
        self.assertFalse(FilenameParser.is_signed_status('review'))

    def test_normalize_path_segment(self):
        """Test path segment normalization."""
        # Test normal case
        self.assertEqual(FilenameParser.normalize_path_segment('ClientName'), 'ClientName')
        
        # Test with spaces
        self.assertEqual(FilenameParser.normalize_path_segment('Client Name'), 'Client_Name')
        
        # Test with special characters (removes them)
        self.assertEqual(FilenameParser.normalize_path_segment('Client/Name'), 'ClientName')


class TestFileStabilityChecker(unittest.TestCase):
    """Test cases for FileStabilityChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.checker = FileStabilityChecker(timeout=0.5, check_interval=0.1)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_file_stability_stable_file(self):
        """Test stability check for a stable file."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, 'test.pdf')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        # File should be stable
        self.assertTrue(self.checker.wait_for_stability(Path(test_file)))
    
    def test_file_stability_nonexistent_file(self):
        """Test stability check for nonexistent file."""
        test_file = os.path.join(self.temp_dir, 'nonexistent.pdf')
        
        # Should return False for nonexistent file
        self.assertFalse(self.checker.wait_for_stability(Path(test_file)))


class TestPDFMover(unittest.TestCase):
    """Test cases for PDFMover class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.workplace = os.path.join(self.temp_dir, 'workplace')
        self.destination = os.path.join(self.temp_dir, 'destination')
        os.makedirs(self.workplace)
        os.makedirs(self.destination)
        
        self.mover = PDFMover(self.destination)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_move_signed_pdf_dry_run(self):
        """Test PDF moving in dry run mode."""
        # Create mover in dry run mode
        mover = PDFMover(self.destination, dry_run=True)
        
        # Create test file
        test_file = Path(self.workplace) / 'contract_Test_2024-01-01_signed.pdf'
        test_file.write_text('test content')
        
        parsed = {
            'doc': 'contract',
            'client': 'Test',
            'date': '2024-01-01',
            'status': 'signed'
        }
        
        # Process should succeed but not move file
        result = mover.move_signed_pdf(test_file, parsed)
        self.assertTrue(result)
        self.assertTrue(test_file.exists())  # File should still exist
    
    def test_move_signed_pdf_success(self):
        """Test successful PDF moving."""
        # Create test file
        test_file = Path(self.workplace) / 'contract_Test_2024-01-01_signed.pdf'
        test_file.write_text('test content')
        
        parsed = {
            'doc': 'contract',
            'client': 'Test',
            'date': '2024-01-01',
            'status': 'signed'
        }
        
        result = self.mover.move_signed_pdf(test_file, parsed)
        self.assertTrue(result)
        
        # Check that file was moved to correct location
        expected_path = Path(self.destination) / 'contract' / 'Test' / '2024-01-01' / 'signed' / 'contract_Test_2024-01-01_signed.pdf'
        self.assertTrue(expected_path.exists())
        self.assertFalse(test_file.exists())  # Original should be gone


class TestPDFWatchHandler(unittest.TestCase):
    """Test cases for PDFWatchHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.workplace = os.path.join(self.temp_dir, 'workplace')
        self.destination = os.path.join(self.temp_dir, 'destination')
        os.makedirs(self.workplace)
        os.makedirs(self.destination)
        
        # Create mocks
        self.mover = MagicMock()
        self.stability_checker = MagicMock()
        self.handler = PDFWatchHandler(self.mover, self.stability_checker)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_on_created_with_pdf(self):
        """Test file creation event with PDF."""
        # Create a mock event
        from watchdog.events import FileCreatedEvent
        test_file = os.path.join(self.workplace, 'test.pdf')
        event = FileCreatedEvent(test_file)
        
        # Mock stability checker to return True
        self.stability_checker.wait_for_stability.return_value = True
        
        # Mock FilenameParser methods
        with patch('signed_watcher.FilenameParser.parse_filename') as mock_parse, \
             patch('signed_watcher.FilenameParser.is_signed_status') as mock_signed:
            
            mock_parse.return_value = {'doc': 'test', 'status': 'signed'}
            mock_signed.return_value = True
            
            self.handler.on_created(event)
            
            # Should have called the process chain
            self.stability_checker.wait_for_stability.assert_called_once()
    
    def test_on_created_with_non_pdf(self):
        """Test file creation event with non-PDF."""
        from watchdog.events import FileCreatedEvent
        test_file = os.path.join(self.workplace, 'test.txt')
        event = FileCreatedEvent(test_file)
        
        self.handler.on_created(event)
        
        # Should not process non-PDF files
        self.stability_checker.wait_for_stability.assert_not_called()


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests
    unittest.main()
