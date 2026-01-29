# Written Questions

## Question 1: Pipeline Failure Recovery Strategy

**Question:** Your data pipeline delivers files to an external partner via SFTP every night at 2 AM. Last night, the SFTP transfer succeeded, but the Glue job failed to update the internal tracking table that records "last successful delivery date" due to a transient Redshift connection timeout. Now your pipeline thinks yesterday's data wasn't delivered and is attempting to re-send it, but the partner's system rejects duplicate deliveries. 

Describe one specific idempotency mechanism you would implement to prevent duplicate deliveries if the tracking table update fails after successful SFTP transfer. Explain where you would place this mechanism in the pipeline.

**Answer:**

To prevent duplicate deliveries when the tracking table update fails after a successful SFTP transfer, I would implement a **content-based idempotency check using file checksums (MD5/SHA256)** combined with a **local delivery manifest**.

**Specific Mechanism:**

1. **Pre-Upload Checksum Generation**: Before uploading to SFTP, calculate a checksum (MD5 or SHA256) of the entire dataset or a manifest file containing file names and sizes. This checksum uniquely identifies the data batch being delivered.

2. **Remote Checksum Verification**: After successful SFTP upload, immediately check if a file with the same checksum already exists on the remote server (e.g., upload a `.checksum` file alongside the data files, or query the remote directory for existing checksum files).

3. **Local Delivery Manifest**: Maintain a local JSON manifest file (similar to `delivery_manifest.json` already implemented) that records:
   - Delivery timestamp
   - Checksum of delivered data
   - Remote file paths
   - Delivery status (success/failed)

4. **Idempotency Check Before Upload**: Before attempting SFTP upload, check:
   - If the checksum exists in the local manifest with status "success"
   - If a checksum file with the same value exists on the remote SFTP server
   - If either condition is true, skip the upload and log a warning

**Placement in Pipeline:**

The idempotency mechanism should be placed in **two locations**:

1. **Before SFTP Upload** (in `sftp_delivery.py`): Add a `check_existing_delivery()` function that:
   - Calculates checksum of the data to be delivered
   - Queries the local manifest for previous successful deliveries with the same checksum
   - Optionally checks the remote SFTP server for existing checksum files
   - Returns `True` if delivery already exists, `False` otherwise
   - This check should be called at the start of `deliver_to_sftp()` before `upload_with_retry()`

2. **After Successful Upload** (in `sftp_delivery.py`): Modify `upload_with_retry()` to:
   - Calculate and store the checksum in the delivery metadata
   - Upload a `.checksum` file to the remote server containing the checksum value
   - Update the local manifest with the checksum and status

**Example Implementation Flow:**

```python
def deliver_to_sftp(config_path, local_path):
    # 1. Calculate checksum of data to be delivered
    data_checksum = calculate_checksum(local_path)
    
    # 2. Check if this data was already successfully delivered
    if check_existing_delivery(data_checksum, manifest_path):
        print(f"Data with checksum {data_checksum} already delivered. Skipping upload.")
        return
    
    # 3. Proceed with upload
    metadata = upload_with_retry(sftp_config, local_path, remote_dir)
    metadata["checksum"] = data_checksum
    
    # 4. Upload checksum file to remote server
    upload_checksum_file(sftp_config, data_checksum, remote_dir)
    
    # 5. Update local manifest (this happens even if tracking table update fails)
    create_delivery_manifest(metadata)
```

**Why This Works:**

- **Decoupled from tracking table**: The local manifest and remote checksum files are independent of the Redshift tracking table, so they persist even if the database update fails.
- **Content-based**: Uses checksums to identify identical data batches, preventing duplicate deliveries even if the pipeline runs multiple times.
- **Recoverable**: If the tracking table update fails, the next pipeline run will check the local manifest and skip re-uploading the same data.
- **Auditable**: The manifest provides a complete history of deliveries for troubleshooting.

This approach ensures that even if the Glue job fails to update the tracking table after a successful SFTP transfer, the pipeline will detect the previous successful delivery and avoid duplicate uploads.
