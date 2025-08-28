#!/usr/bin/env python3
"""
Unit tests for the signed PDF watcher.
"""

import unittest
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from signed_watcher import (
    FilenameParser,
    FileStabilityChecker,
    PDFMover,
    PDFWatchHandler
)


class TestFilenameParser(unittest.TestCase):
    """Test cases for FilenameParser class."""
    
    def test_valid_filename_parsing(self):
        """Test parsing of valid filenames."""
        test_cases = [
            {
                'filename': 'contract_ClientName_2024-01-15_signed.pdf',
                'expected': {
                    'doc': 'contract',
                    'client': 'ClientName',
                    'date': '2024-01-15',
                    'status': 'signed'
                }
            },
            {
                'filename': 'NDA_Startup_Inc_20240115_executed.pdf',
                'expected': {
                    'doc': 'NDA',
                    'client': 'Startup_Inc',
                    'date': '20240115',
                    'status': 'executed'
                }
            },
            {
                'filename': 'agreement_test_client_2024-12-31_final.pdf',
                'expected': {
                    'doc': 'agreement',
                    'client': 'test_client',
                    'date': '2024-12-31',
                    'status': 'final'
                }
            }
        ]
        
        for case in test_cases:
            with self.subTest(filename=case['filename']):
                result = FilenameParser.parse_filename(case['filename'])
                self.assertIsNotNone(result)
                self.assertEqual(result, case['expected'])
    
    def test_invalid_filename_parsing(self):
        """Test parsing of invalid filenames."""
        invalid_filenames = [
            'contract.pdf',
            'contract_client.pdf',
            'contract_client_2024.pdf',
            'contract_client_invalid_date_signed.pdf',
            'no_extension',
            'contract_client_2024-01-15_signed.txt'
        ]
        
        for filename in invalid_filenames:
            with self.subTest(filename=filename):
                result = FilenameParser.parse_filename(filename)
                self.assertIsNone(result)
    
    def test_signed_status_detection(self):
        """Test detection of signed status."""
        signed_statuses = [
            'signed',
            'SIGNED',
            'Signed',
            'executed',
            'EXECUTED',
            'final',
            'FINAL',
            'contract_signed',
            'signed_copy',
            'fully_executed',
            'final_version'
        ]
        
        for status in signed_statuses:
            with self.subTest(status=status):
                self.assertTrue(FilenameParser.is_signed_status(status))
        
        unsigned_statuses = [
            'draft',
            'pending',
            'review',
            'unsigned',
            'template'
        ]
        
        for status in unsigned_statuses:
            with self.subTest(status=status):
                self.assertFalse(FilenameParser.is_signed_status(status))
    
    def test_path_segment_normalization(self):
        """Test normalization of path segments."""
        test_cases = [
            ('Client Name', 'Client_Name'),
            ('Company/LLC', 'CompanyLLC'),
            ('Test<>Client', 'TestClient'),
            ('  spaces  ', 'spaces'),
            ('Multi   Space   Name', 'Multi_Space_Name'),
            ('file:name', 'filename'),
            ('valid_name', 'valid_name')
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                result = FilenameParser.normalize_path_segment(input_val)
                self.assertEqual(result, expected)


class TestFileStabilityChecker(unittest.TestCase):
    """Test cases for FileStabilityChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.test_file = self.temp_path / 'test.pdf'
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_stable_file(self):
        """Test detection of stable file."""
        # Create a file with content
        self.test_file.write_text('test content')
        
        checker = FileStabilityChecker(timeout=2.0, check_interval=0.1)
        result = checker.wait_for_stability(self.test_file)
        self.assertTrue(result)
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        checker = FileStabilityChecker(timeout=1.0)
        result = checker.wait_for_stability(self.test_file)
        self.assertFalse(result)
    
    def test_growing_file_timeout(self):
        """Test timeout when file keeps growing."""
        checker = FileStabilityChecker(timeout=0.5, check_interval=0.1)
        
        # Create file and keep modifying it
        self.test_file.write_text('initial')
        
        def keep_growing():
            time.sleep(0.2)
            self.test_file.write_text('growing content')
            time.sleep(0.2)
            self.test_file.write_text('still growing content')
        
        import threading
        thread = threading.Thread(target=keep_growing)
        thread.start()
        
        result = checker.wait_for_stability(self.test_file)
        thread.join()
        
        # Should timeout since file keeps changing
        self.assertFalse(result)


class TestPDFMover(unittest.TestCase):
    """Test cases for PDFMover class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.temp_dir) / 'source'
        self.dest_dir = Path(self.temp_dir) / 'dest'
        self.source_dir.mkdir()
        self.dest_dir.mkdir()
        
        self.test_file = self.source_dir / 'contract_ClientName_2024-01-15_signed.pdf'
        self.test_file.write_text('test pdf content')
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_successful_move(self):
        """Test successful file move."""
        mover = PDFMover(self.dest_dir, dry_run=False)
        parsed_info = {
            'doc': 'contract',
            'client': 'ClientName',
            'date': '2024-01-15',
            'status': 'signed'
        }
        
        result = mover.move_signed_pdf(self.test_file, parsed_info)
        self.assertTrue(result)
        
        # Check file was moved to correct location (form/client/date/status)
        expected_path = self.dest_dir / 'contract' / 'ClientName' / '2024-01-15' / 'signed' / self.test_file.name
        self.assertTrue(expected_path.exists())
        self.assertFalse(self.test_file.exists())
    
    def test_dry_run_mode(self):
        """Test dry run mode doesn't actually move files."""
        mover = PDFMover(self.dest_dir, dry_run=True)
        parsed_info = {
            'doc': 'contract',
            'client': 'ClientName',
            'date': '2024-01-15',
            'status': 'signed'
        }
        
        result = mover.move_signed_pdf(self.test_file, parsed_info)
        self.assertTrue(result)
        
        # Original file should still exist in dry run
        self.assertTrue(self.test_file.exists())
        
        # Destination should not exist
        expected_path = self.dest_dir / 'contract' / 'ClientName' / '2024-01-15' / 'signed' / self.test_file.name
        self.assertFalse(expected_path.exists())
    
    def test_duplicate_handling(self):
        """Test handling of duplicate filenames."""
        mover = PDFMover(self.dest_dir, dry_run=False)
        parsed_info = {
            'doc': 'contract',
            'client': 'ClientName',
            'date': '2024-01-15',
            'status': 'signed'
        }
        
        # Create the destination file first
        dest_path = self.dest_dir / 'contract' / 'ClientName' / '2024-01-15' / 'signed'
        dest_path.mkdir(parents=True)
        existing_file = dest_path / self.test_file.name
        existing_file.write_text('existing content')
        
        # Move should succeed and create timestamped version
        result = mover.move_signed_pdf(self.test_file, parsed_info)
        self.assertTrue(result)
        
        # Original destination file should still exist
        self.assertTrue(existing_file.exists())
        
        # New file should exist with timestamp
        files_in_dest = list(dest_path.glob('*.pdf'))
        self.assertEqual(len(files_in_dest), 2)
        
        # Source file should be gone
        self.assertFalse(self.test_file.exists())
    
    def test_path_normalization(self):
        """Test path normalization in destination."""
        mover = PDFMover(self.dest_dir, dry_run=False)
        parsed_info = {
            'doc': 'contract file',
            'client': 'Client/Name',
            'date': '2024-01-15',
            'status': 'signed'
        }
        
        result = mover.move_signed_pdf(self.test_file, parsed_info)
        self.assertTrue(result)
        
        # Check normalized path was created (form/client/date/status)
        expected_path = self.dest_dir / 'contract_file' / 'ClientName' / '2024-01-15' / 'signed' / self.test_file.name
        self.assertTrue(expected_path.exists())


class TestPDFWatchHandler(unittest.TestCase):
    """Test cases for PDFWatchHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mover_mock = MagicMock()
        self.stability_checker_mock = MagicMock()
        self.handler = PDFWatchHandler(self.mover_mock, self.stability_checker_mock)
    
    def test_process_valid_signed_pdf(self):
        """Test processing of valid signed PDF."""
        test_file = Path('/test/contract_ClientName_2024-01-15_signed.pdf')
        
        # Mock stability checker to return True
        self.stability_checker_mock.wait_for_stability.return_value = True
        
        # Mock successful move
        self.mover_mock.move_signed_pdf.return_value = True
        
        with patch('signed_watcher.logging'):
            self.handler._process_file(test_file)
        
        # Verify stability check was called
        self.stability_checker_mock.wait_for_stability.assert_called_once_with(test_file)
        
        # Verify move was attempted
        self.mover_mock.move_signed_pdf.assert_called_once()
    
    def test_process_non_pdf_file(self):
        """Test processing of non-PDF file."""
        test_file = Path('/test/document.txt')
        
        with patch('signed_watcher.logging'):
            self.handler._process_file(test_file)
        
        # Should not attempt to move non-PDF files
        self.mover_mock.move_signed_pdf.assert_not_called()
    
    def test_process_invalid_filename(self):
        """Test processing of PDF with invalid filename pattern."""
        test_file = Path('/test/invalid_filename.pdf')
        
        with patch('signed_watcher.logging'):
            self.handler._process_file(test_file)
        
        # Should not attempt to move files with invalid patterns
        self.mover_mock.move_signed_pdf.assert_not_called()
    
    def test_process_unsigned_pdf(self):
        """Test processing of unsigned PDF."""
        test_file = Path('/test/contract_ClientName_2024-01-15_draft.pdf')
        
        with patch('signed_watcher.logging'):
            self.handler._process_file(test_file)
        
        # Should not attempt to move unsigned files
        self.mover_mock.move_signed_pdf.assert_not_called()
    
    def test_process_unstable_file(self):
        """Test processing of file that doesn't stabilize."""
        test_file = Path('/test/contract_ClientName_2024-01-15_signed.pdf')
        
        # Mock stability checker to return False (timeout)
        self.stability_checker_mock.wait_for_stability.return_value = False
        
        with patch('signed_watcher.logging'):
            self.handler._process_file(test_file)
        
        # Should not attempt to move unstable files
        self.mover_mock.move_signed_pdf.assert_not_called()


if __name__ == '__main__':
    unittest.main()