"""
Unit tests for SFTP delivery with retry logic.
"""
import pytest
import os
import sys
import json
import shutil
import tempfile
import time
from unittest.mock import Mock, patch, MagicMock
import pysftp

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sftp_delivery import (
    upload_with_retry,
    create_delivery_manifest,
    SFTPDeliveryException,
    get_file_size,
    get_directory_size,
    _create_sftp_connection,
    _upload_files
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for testing."""
    file_path = os.path.join(temp_dir, "test_file.txt")
    with open(file_path, 'w') as f:
        f.write("Test content for SFTP upload")
    return file_path


@pytest.fixture
def sample_directory(temp_dir):
    """Create a sample directory structure for testing."""
    dir_path = os.path.join(temp_dir, "test_dir")
    os.makedirs(dir_path)

    # Create some files in the directory
    for i in range(3):
        file_path = os.path.join(dir_path, f"file_{i}.txt")
        with open(file_path, 'w') as f:
            f.write(f"Content of file {i}")

    return dir_path


@pytest.fixture
def sftp_config():
    """Sample SFTP configuration."""
    return {
        "host": "localhost",
        "port": 2222,
        "username": "testuser",
        "password": "testpass",
        "remote_dir": "/uploads",
        "retry_attempts": 3,
        "retry_backoff_base": 1
    }


def test_get_file_size(sample_file):
    """Test file size calculation."""
    size = get_file_size(sample_file)
    assert size > 0
    assert size == len("Test content for SFTP upload")


def test_get_directory_size(sample_directory):
    """Test directory size calculation."""
    size = get_directory_size(sample_directory)
    assert size > 0


def test_upload_with_retry_success_first_attempt(sample_file, sftp_config, temp_dir):
    """Test successful upload on first attempt."""
    with patch('sftp_delivery._create_sftp_connection') as mock_create_conn, \
         patch('sftp_delivery._upload_files') as mock_upload:
        # Mock SFTP connection
        mock_sftp = MagicMock()
        mock_create_conn.return_value = mock_sftp
        mock_upload.return_value = ["test_file.txt"]

        # Upload file
        metadata = upload_with_retry(sftp_config, sample_file, "/uploads")

        # Verify metadata
        assert metadata["attempt_number"] == 1
        assert "test_file.txt" in metadata["files_uploaded"]
        assert metadata["local_size"] > 0
        assert "timestamp" in metadata

        # Verify helper functions were called
        mock_create_conn.assert_called_once()
        mock_upload.assert_called_once()
        mock_sftp.close.assert_called_once()


def test_upload_with_retry_fails_then_succeeds(sample_file, sftp_config):
    """Test that retry logic works when first attempts fail."""
    with patch('sftp_delivery._create_sftp_connection') as mock_create_conn, \
         patch('sftp_delivery._upload_files') as mock_upload, \
         patch('time.sleep'):  # Mock sleep to speed up test

        # First attempt fails, second succeeds
        mock_sftp = MagicMock()
        mock_create_conn.return_value = mock_sftp
        mock_upload.side_effect = [
            Exception("Connection timeout"),
            ["test_file.txt"]  # Success on second attempt
        ]

        metadata = upload_with_retry(sftp_config, sample_file, "/uploads")

        # Should succeed on second attempt
        assert metadata["attempt_number"] == 2
        assert "test_file.txt" in metadata["files_uploaded"]


def test_upload_with_retry_exhausts_retries(sample_file, sftp_config):
    """Test that exception is raised after all retries fail."""
    with patch('sftp_delivery._create_sftp_connection') as mock_create_conn, \
         patch('sftp_delivery._upload_files') as mock_upload, \
         patch('time.sleep'):

        # All attempts fail
        mock_sftp = MagicMock()
        mock_create_conn.return_value = mock_sftp
        mock_upload.side_effect = Exception("Connection refused")

        with pytest.raises(SFTPDeliveryException):
            upload_with_retry(sftp_config, sample_file, "/uploads")


def test_upload_with_retry_exponential_backoff(sample_file, sftp_config):
    """Test that exponential backoff is applied correctly."""
    with patch('sftp_delivery._create_sftp_connection') as mock_create_conn, \
         patch('sftp_delivery._upload_files') as mock_upload, \
         patch('time.sleep') as mock_sleep:

        # All attempts fail
        mock_sftp = MagicMock()
        mock_create_conn.return_value = mock_sftp
        mock_upload.side_effect = Exception("Connection refused")

        try:
            upload_with_retry(sftp_config, sample_file, "/uploads")
        except SFTPDeliveryException:
            pass

        # Check that sleep was called with increasing delays
        # First retry: 1s, Second retry: 2s
        assert mock_sleep.call_count == 2
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert calls[0] == 1  # 1 * 2^0
        assert calls[1] == 2  # 1 * 2^1


def test_upload_with_retry_handles_directory(sample_directory, sftp_config):
    """Test uploading a directory."""
    with patch('sftp_delivery._create_sftp_connection') as mock_create_conn, \
         patch('sftp_delivery._upload_files') as mock_upload:
        mock_sftp = MagicMock()
        mock_create_conn.return_value = mock_sftp
        mock_upload.return_value = ["file_0.txt", "file_1.txt", "file_2.txt"]

        metadata = upload_with_retry(sftp_config, sample_directory, "/uploads")

        # Verify directory upload was attempted
        assert metadata["attempt_number"] == 1
        assert len(metadata["files_uploaded"]) == 3
        mock_upload.assert_called_once()


def test_create_delivery_manifest(temp_dir):
    """Test creation of delivery manifest."""
    manifest_path = os.path.join(temp_dir, "manifest.json")

    metadata1 = {
        "timestamp": "2023-01-01T10:00:00",
        "files_uploaded": ["file1.txt"],
        "status": "success"
    }

    metadata2 = {
        "timestamp": "2023-01-01T11:00:00",
        "files_uploaded": ["file2.txt"],
        "status": "success"
    }

    # Create first manifest entry
    create_delivery_manifest(metadata1, manifest_path)
    assert os.path.exists(manifest_path)

    # Add second entry
    create_delivery_manifest(metadata2, manifest_path)

    # Verify both entries are in manifest
    with open(manifest_path, 'r') as f:
        manifests = json.load(f)

    assert len(manifests) == 2
    assert manifests[0]["files_uploaded"] == ["file1.txt"]
    assert manifests[1]["files_uploaded"] == ["file2.txt"]


def test_upload_with_retry_handles_nonexistent_path(sftp_config):
    """Test that appropriate error is raised for nonexistent path."""
    with patch('sftp_delivery._create_sftp_connection') as mock_create_conn, \
         patch('sftp_delivery._upload_files') as mock_upload:
        mock_sftp = MagicMock()
        mock_create_conn.return_value = mock_sftp
        mock_upload.side_effect = FileNotFoundError("Path does not exist")

        with pytest.raises(SFTPDeliveryException):
            upload_with_retry(sftp_config, "/nonexistent/path", "/uploads")
