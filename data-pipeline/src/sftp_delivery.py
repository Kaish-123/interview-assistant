"""
SFTP Delivery Module with Retry Logic.
Securely transfers files to remote SFTP server with retry and validation.
"""
import pysftp
import paramiko
import os
import time
import json
from datetime import datetime
from pathlib import Path


class SFTPDeliveryException(Exception):
    """Raised when SFTP delivery fails after all retries."""
    pass


def get_file_size(file_path: str) -> int:
    """Get size of a file in bytes."""
    return os.path.getsize(file_path)


def get_directory_size(directory: str) -> int:
    """Get total size of all files in a directory recursively."""
    total_size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
    return total_size


def _create_sftp_connection(host: str, port: int, username: str, password: str):
    """
    Helper function to create SFTP connection with proper configuration.

    Args:
        host: SFTP server hostname
        port: SFTP server port
        username: SFTP username
        password: SFTP password

    Returns:
        pysftp.Connection object
    """
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  # Disable host key checking for testing

    return pysftp.Connection(
        host=host,
        port=port,
        username=username,
        password=password,
        cnopts=cnopts
    )


def _upload_files(sftp, local_path: str, remote_dir: str) -> list:
    """
    Helper function to upload files/directories via SFTP.

    Args:
        sftp: Active SFTP connection
        local_path: Local file or directory to upload
        remote_dir: Remote directory to upload to

    Returns:
        List of uploaded file names
    """
    uploaded_files = []

    # Create remote directory if it doesn't exist
    if not sftp.exists(remote_dir):
        sftp.makedirs(remote_dir)

    # Handle directory upload
    if os.path.isdir(local_path):
        for root, dirs, files in os.walk(local_path):
            for file in files:
                local_file = os.path.join(root, file)
                # Calculate relative path to maintain directory structure
                rel_path = os.path.relpath(local_file, local_path)
                remote_file = os.path.join(remote_dir, rel_path).replace("\\", "/")

                # Create remote subdirectories if needed
                remote_file_dir = os.path.dirname(remote_file)
                if not sftp.exists(remote_file_dir):
                    sftp.makedirs(remote_file_dir)

                sftp.put(local_file, remote_file)
                uploaded_files.append(rel_path)
    else:
        # Single file upload
        remote_file = os.path.join(remote_dir, os.path.basename(local_path)).replace("\\", "/")
        sftp.put(local_path, remote_file)
        uploaded_files.append(os.path.basename(local_path))

    return uploaded_files


def upload_with_retry(sftp_config: dict, local_path: str, remote_dir: str) -> dict:
    """
    Upload file or directory to SFTP server with retry logic.

    Args:
        sftp_config: Dictionary with SFTP connection parameters
            - host: SFTP server hostname
            - port: SFTP server port
            - username: SFTP username
            - password: SFTP password
            - retry_attempts: Maximum number of retry attempts
            - retry_backoff_base: Base delay in seconds for exponential backoff
        local_path: Path to local file or directory to upload
        remote_dir: Remote directory to upload to

    Returns:
        Dictionary with delivery metadata including:
            - timestamp: When the upload completed
            - files_uploaded: List of uploaded files
            - attempt_number: Which attempt succeeded
            - local_size: Size of uploaded data in bytes

    Raises:
        SFTPDeliveryException: If upload fails after all retries
    """
    max_attempts = sftp_config.get("retry_attempts", 3)
    backoff_base = sftp_config.get("retry_backoff_base", 1)
    
    # Calculate local size
    if os.path.isdir(local_path):
        local_size = get_directory_size(local_path)
    else:
        local_size = get_file_size(local_path)
    
    last_exception = None
    
    # Retry loop with exponential backoff
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"SFTP upload attempt {attempt}/{max_attempts}...")
            
            # Create SFTP connection
            sftp = _create_sftp_connection(
                host=sftp_config["host"],
                port=sftp_config["port"],
                username=sftp_config["username"],
                password=sftp_config["password"]
            )
            
            try:
                # Upload files
                uploaded_files = _upload_files(sftp, local_path, remote_dir)
                
                # Success - return metadata
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "files_uploaded": uploaded_files,
                    "attempt_number": attempt,
                    "local_size": local_size
                }
                
                print(f"✓ Upload successful on attempt {attempt}")
                return metadata
                
            finally:
                # Always close the connection
                sftp.close()
                
        except Exception as e:
            last_exception = e
            print(f"✗ Attempt {attempt} failed: {str(e)}")
            
            # If this is not the last attempt, wait before retrying
            if attempt < max_attempts:
                # Exponential backoff: delay = base * 2^(attempt-1)
                delay = backoff_base * (2 ** (attempt - 1))
                print(f"  Waiting {delay}s before retry...")
                time.sleep(delay)
            else:
                # All retries exhausted
                print(f"✗ All {max_attempts} attempts failed")
                raise SFTPDeliveryException(
                    f"SFTP upload failed after {max_attempts} attempts. Last error: {str(last_exception)}"
                ) from last_exception
    
    # This should never be reached, but just in case
    raise SFTPDeliveryException(
        f"SFTP upload failed after {max_attempts} attempts. Last error: {str(last_exception)}"
    ) from last_exception


def create_delivery_manifest(metadata: dict, manifest_path: str = "output/delivery_manifest.json") -> None:
    """
    Create a delivery manifest file tracking what was sent and when.

    Args:
        metadata: Dictionary with delivery metadata
        manifest_path: Path to write manifest file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)

    # Load existing manifest if it exists
    manifests = []
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifests = json.load(f)

    # Append new delivery
    manifests.append(metadata)

    # Write updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifests, f, indent=2)

    print(f"Delivery manifest updated at {manifest_path}")


def deliver_to_sftp(config_path: str = "config/config.json", local_path: str = None) -> None:
    """
    Main delivery function: upload to SFTP and create manifest.

    Args:
        config_path: Path to configuration file
        local_path: Path to file/directory to upload (overrides config)
    """
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)

    sftp_config = config["sftp"]
    remote_dir = sftp_config["remote_dir"]

    # Use provided path or default from config
    if local_path is None:
        local_path = config["output"]["path"]

    # Upload with retry
    metadata = upload_with_retry(sftp_config, local_path, remote_dir)

    # Create delivery manifest
    create_delivery_manifest(metadata)

    print(f"Delivery completed successfully")


if __name__ == "__main__":
    deliver_to_sftp()
