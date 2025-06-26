import boto3
import os
import logging
import gzip
import shutil
from pathlib import Path
from django.conf import settings
from datetime import datetime, timedelta

class S3FileFetcher:
    def __init__(self):
        """Initialize S3 Client using credentials from settings."""
        self.logger = logging.getLogger(__name__)  # ✅ Initialize logger at the beginning

        # Fetch AWS credentials and settings from environment variables
        self.bucket_name = settings.BUCKET_NAME
        self.region = settings.BUCKET_REGION
        self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        self.bucket_prefix = settings.BUCKET_PREFIX

        if not all([self.bucket_name, self.region, self.aws_access_key_id, self.aws_secret_access_key]):
            self.logger.error("Missing AWS credentials or configurations.")
            raise ValueError("Missing AWS credentials or configurations.")

        # ✅ Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region
            )
            self.logger.info(f"S3 client initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    def list_files(self, prefix: str):
        """List all files in the S3 bucket under the given prefix."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
                self.logger.info(f"Found {len(files)} files in {prefix}")
                return files
            else:
                self.logger.warning(f"No files found in {prefix}")
                return []
        except Exception as e:
            self.logger.error(f"Error listing files: {str(e)}")
            raise

    def download_file(self, s3_key: str, local_path: str):
        """Download a specific file from S3."""
        try:
            os.makedirs(local_path, exist_ok=True)
            local_filename = os.path.join(local_path, os.path.basename(s3_key))
            self.s3_client.download_file(self.bucket_name, s3_key, local_filename)
            self.logger.info(f"File downloaded successfully: {local_filename}")
            return local_filename
        except Exception as e:
            self.logger.error(f"Error downloading file: {str(e)}")
            raise

def get_current_month_gz_files(s3_fetcher: S3FileFetcher):
    """Fetch .gz files for the current billing month from the S3 bucket."""
    today = datetime.today()
    first_day_of_prev_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    first_day_of_current_month = today.replace(day=1)

    # ✅ Use the bucket prefix from settings
    prefix = f"/{first_day_of_prev_month.strftime('%Y%m%d')}-{first_day_of_current_month.strftime('%Y%m%d')}/"
    prefix = s3_fetcher.bucket_prefix + prefix  # Correct bucket prefix

    logging.info(f"Looking for files in prefix: {prefix}")

    # Fetch and filter .gz files
    all_files = s3_fetcher.list_files(prefix)
    gz_files = [file for file in all_files if file.endswith('.gz')]

    if not gz_files:
        logging.warning(f"No .gz files found.")
        return []

    # ✅ Save .gz files in `gz_downloads/`
    gz_download_path = os.path.join(settings.BASE_DIR, "gz_downloads")
    os.makedirs(gz_download_path, exist_ok=True)

    downloaded_files = []
    for file in gz_files:
        try:
            downloaded_file = s3_fetcher.download_file(file, gz_download_path)
            downloaded_files.append(downloaded_file)
        except Exception as e:
            logging.error(f"Error downloading {file}: {e}")

    return downloaded_files

def get_this_month_csv_bills(s3_fetcher: S3FileFetcher):
    """Fetch, extract, and delete .gz billing files for the current month from S3."""
    gz_download_path = os.path.join(settings.BASE_DIR, "gz_downloads")
    extracted_path = os.path.join(settings.BASE_DIR, "extracted_csvs")

    os.makedirs(gz_download_path, exist_ok=True)
    os.makedirs(extracted_path, exist_ok=True)

    # ✅ Fetch .gz files and save in `gz_downloads/`
    downloaded_files = get_current_month_gz_files(s3_fetcher)
    if not downloaded_files:
        logging.warning(f"No .gz files downloaded.")
        return []

    logging.info(f"Downloaded {len(downloaded_files)} .gz files. Extracting...")

    extracted_files = []
    for gz_file in downloaded_files:
        try:
            if not gz_file.endswith('.gz'):
                logging.warning(f"Skipping non-gz file: {gz_file}")
                continue

            csv_filename = os.path.basename(gz_file).replace('.gz', '')
            extracted_csv_path = os.path.join(extracted_path, csv_filename)

            with gzip.open(gz_file, 'rb') as f_in:
                with open(extracted_csv_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # ✅ Ensure the file was actually extracted
            if os.path.exists(extracted_csv_path):
                logging.info(f"✅ Extracted and saved: {extracted_csv_path}")
                extracted_files.append(extracted_csv_path)
            else:
                logging.error(f"❌ Extraction failed, file not found: {extracted_csv_path}")

            # ✅ Delete the .gz file immediately after extraction
            os.remove(gz_file)
            logging.info(f"🗑️ Deleted: {gz_file}")

        except Exception as e:
            logging.error(f"⚠️ Error extracting {gz_file}: {e}")

    if not extracted_files:
        logging.error("❌ No CSV files were extracted. Check file permissions or paths.")
        return []

    return extracted_files
