"""
Test utilities and fixtures for the file organizer tests.
"""

import os
from pathlib import Path
import shutil
import tempfile


class TestFixtures:
    """Helper class for managing test fixtures."""
    
    @classmethod
    def get_fixtures_dir(cls) -> Path:
        """Get the path to the test fixtures directory."""
        return Path(__file__).parent / 'fixtures'
    
    @classmethod
    def get_sample_workplace(cls) -> Path:
        """Get the path to sample workplace files."""
        return cls.get_fixtures_dir() / 'workplace'
    
    @classmethod
    def get_sample_destination(cls) -> Path:
        """Get the path to sample destination structure."""
        return cls.get_fixtures_dir() / 'destination'
    
    @classmethod
    def create_temp_workplace(cls, temp_dir: Path) -> Path:
        """
        Create a temporary workplace directory with sample files.
        
        Args:
            temp_dir: Temporary directory to create workplace in
            
        Returns:
            Path to the created workplace directory
        """
        workplace = temp_dir / 'workplace'
        workplace.mkdir(exist_ok=True)
        
        # Copy sample files from fixtures
        fixtures_workplace = cls.get_sample_workplace()
        if fixtures_workplace.exists():
            for file_path in fixtures_workplace.iterdir():
                if file_path.is_file():
                    shutil.copy2(file_path, workplace)
        
        return workplace
    
    @classmethod
    def create_test_pdf(cls, filepath: Path, content: str = "Test PDF content") -> Path:
        """
        Create a test PDF file with given content.
        
        Args:
            filepath: Path where to create the file
            content: Content to write to the file
            
        Returns:
            Path to the created file
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)
        return filepath
    
    @classmethod
    def get_sample_filenames(cls) -> list[str]:
        """Get a list of sample PDF filenames for testing."""
        return [
            "contract_StartupAlpha_2024-08-21_signed.pdf",
            "NDA_TechCorp_20240815_executed.pdf", 
            "employment_John_Doe_LLC_2024-06-15_fully_signed.pdf",
            "service_ClientBeta_2024-07-30_final.pdf",
            "contract_StartupGamma_2024-08-20_draft.pdf",  # Not signed
            "invalid_filename.pdf",  # Invalid format
            "not_a_pdf.txt"  # Not a PDF
        ]
