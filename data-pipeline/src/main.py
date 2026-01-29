"""
Main pipeline orchestration script.
Runs ETL pipeline followed by SFTP delivery.
"""
import sys
from etl_pipeline import run_etl_pipeline
from sftp_delivery import deliver_to_sftp


def main():
    """Execute the complete data pipeline."""
    try:
        print("=" * 50)
        print("Starting Data Pipeline")
        print("=" * 50)

        # Step 1: Run ETL Pipeline
        print("\nStep 1: Running ETL Pipeline...")
        output_path = run_etl_pipeline()

        # Step 2: Deliver to SFTP
        print("\nStep 2: Delivering to SFTP...")
        deliver_to_sftp(local_path=output_path)

        print("\n" + "=" * 50)
        print("Pipeline completed successfully!")
        print("=" * 50)

        return 0

    except Exception as e:
        print(f"\nPipeline failed: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
