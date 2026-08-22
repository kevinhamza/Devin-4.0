# Devin/cloud/aws_integration.py # AWS cloud support

import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Generator

# Attempt to import AWS SDK (Boto3)
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    print("WARNING: 'boto3' library not found. AWSIntegration will use non-functional placeholders.")
    BOTO3_AVAILABLE = False
    # Define dummy exception classes if boto3 not installed
    class ClientError(Exception): pass
    class NoCredentialsError(Exception): pass
    class PartialCredentialsError(Exception): pass

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AWSIntegration:
    """
    Provides methods for interacting with various AWS services relevant to Devin.

    Handles initialization of Boto3 clients and basic error handling.
    Relies on Boto3's standard credential discovery chain for authentication.
    """

    def __init__(self, region_name: Optional[str] = None):
        """
        Initializes the AWS Integration class.

        Args:
            region_name (Optional[str]): The AWS region to use. If None, uses the default
                                         configured for the environment (e.g., via AWS_DEFAULT_REGION
                                         environment variable or ~/.aws/config).
        """
        self.region_name = region_name or os.environ.get("AWS_DEFAULT_REGION")
        self._session = None
        self._clients: Dict[str, Any] = {} # Cache for service clients

        if not BOTO3_AVAILABLE:
            logger.error("Boto3 library is not installed. AWS functionality unavailable.")
            # Raise an error or allow graceful degradation depending on requirements
            # raise ImportError("Boto3 is required for AWSIntegration")
        else:
            try:
                # Initialize session - this implicitly checks for basic credential config validity
                self._session = boto3.Session(region_name=self.region_name)
                # Log the configured region (might be None if relying purely on env)
                resolved_region = self._session.region_name
                logger.info(f"AWSIntegration initialized. Session created for region: {resolved_region or 'Default'}")
                # You could optionally check credentials explicitly here, but often it's better
                # to let individual client calls fail if credentials aren't found/valid then.
                # sts = self._session.client('sts')
                # sts.get_caller_identity() # Throws NoCredentialsError etc. if config fails
                # logger.info("AWS Credentials validated successfully via STS.")
            except (NoCredentialsError, PartialCredentialsError) as e:
                logger.error(f"AWS Credentials Error: {e}. Ensure credentials are configured (env vars, ~/.aws/, IAM role).")
                # Depending on how critical AWS is, might raise error or just log
            except Exception as e:
                logger.error(f"Unexpected error initializing Boto3 session: {e}")
                # Handle other potential init errors

    def _get_client(self, service_name: str) -> Optional[Any]:
        """Lazy-loads and returns a Boto3 client for a given service."""
        if not BOTO3_AVAILABLE or self._session is None:
            logger.error(f"Cannot get client for '{service_name}': Boto3 unavailable or session failed.")
            return None

        if service_name not in self._clients:
            try:
                logger.debug(f"Creating Boto3 client for service: {service_name}")
                self._clients[service_name] = self._session.client(service_name)
            except NoCredentialsError as e:
                 logger.error(f"AWS Credentials Error trying to create '{service_name}' client: {e}")
                 return None
            except PartialCredentialsError as e:
                 logger.error(f"AWS Partial Credentials Error trying to create '{service_name}' client: {e}")
                 return None
            except Exception as e:
                logger.error(f"Failed to create Boto3 client for '{service_name}': {e}")
                return None
        return self._clients[service_name]

    # --- S3 Operations ---

    def upload_to_s3(self, bucket_name: str, object_key: str, file_path: str) -> bool:
        """
        Uploads a local file to an S3 bucket.

        Args:
            bucket_name (str): The name of the target S3 bucket.
            object_key (str): The desired key (path/filename) within the bucket.
            file_path (str): The path to the local file to upload.

        Returns:
            bool: True if upload was successful, False otherwise.

        Requires: s3:PutObject IAM permission on the target bucket/key.
        """
        logger.info(f"Attempting to upload '{file_path}' to s3://{bucket_name}/{object_key}")
        if not os.path.exists(file_path):
            logger.error(f"Upload failed: Local file not found at '{file_path}'")
            return False

        s3_client = self._get_client('s3')
        if not s3_client: return False

        try:
            with open(file_path, 'rb') as f:
                s3_client.upload_fileobj(f, bucket_name, object_key)
            logger.info(f"Successfully uploaded to s3://{bucket_name}/{object_key}")
            return True
        except NoCredentialsError:
            logger.error("Upload failed: AWS credentials not found.")
            return False
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            logger.error(f"Upload failed: S3 ClientError (Code: {error_code}): {e}")
            return False
        except Exception as e:
            logger.error(f"Upload failed: Unexpected error: {e}")
            return False

    def download_from_s3(self, bucket_name: str, object_key: str, download_path: str) -> bool:
        """
        Downloads an object from an S3 bucket to a local file.

        Args:
            bucket_name (str): The name of the source S3 bucket.
            object_key (str): The key (path/filename) of the object within the bucket.
            download_path (str): The local path where the file should be saved.

        Returns:
            bool: True if download was successful, False otherwise.

        Requires: s3:GetObject IAM permission on the target object.
        """
        logger.info(f"Attempting to download s3://{bucket_name}/{object_key} to '{download_path}'")
        s3_client = self._get_client('s3')
        if not s3_client: return False

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            s3_client.download_file(bucket_name, object_key, download_path)
            logger.info(f"Successfully downloaded to '{download_path}'")
            return True
        except NoCredentialsError:
            logger.error("Download failed: AWS credentials not found.")
            return False
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == '404':
                 logger.error(f"Download failed: Object not found s3://{bucket_name}/{object_key}")
            else:
                 logger.error(f"Download failed: S3 ClientError (Code: {error_code}): {e}")
            return False
        except Exception as e:
            logger.error(f"Download failed: Unexpected error: {e}")
            return False

    def list_s3_objects(self, bucket_name: str, prefix: str = "") -> Generator[Dict[str, Any], None, None]:
        """
        Lists objects in an S3 bucket, optionally filtered by prefix.

        Args:
            bucket_name (str): The name of the S3 bucket.
            prefix (str): Optional prefix to filter objects by.

        Yields:
            Dict[str, Any]: Dictionary containing information about each object found (Key, Size, LastModified, etc.).

        Requires: s3:ListBucket IAM permission on the target bucket.
        """
        logger.info(f"Listing objects in s3://{bucket_name}/{prefix}*")
        s3_client = self._get_client('s3')
        if not s3_client: return

        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
            count = 0
            for page in page_iterator:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        yield obj
                        count += 1
            logger.info(f"Found {count} objects matching prefix.")
        except NoCredentialsError:
            logger.error("Listing failed: AWS credentials not found.")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            logger.error(f"Listing failed: S3 ClientError (Code: {error_code}): {e}")
        except Exception as e:
            logger.error(f"Listing failed: Unexpected error: {e}")


    # --- Lambda Operations (Conceptual Placeholders) ---

    def invoke_lambda(self, function_name: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Invokes an AWS Lambda function."""
        logger.info(f"Invoking Lambda function '{function_name}' (Conceptual)...")
        lambda_client = self._get_client('lambda')
        if not lambda_client: return None
        # --- Placeholder: Actual invocation ---
        # try:
        #     response = lambda_client.invoke(
        #         FunctionName=function_name,
        #         InvocationType='RequestResponse', # Or 'Event' for async
        #         Payload=json.dumps(payload)
        #     )
        #     status_code = response.get('StatusCode')
        #     if status_code == 200:
        #         response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        #         logger.info("Lambda invocation successful.")
        #         return response_payload
        #     else:
        #         # Handle function errors if present in response
        #         logger.error(f"Lambda invocation returned status {status_code}.")
        #         return None
        # except ClientError as e: logger.error(f"Lambda ClientError: {e}"); return None
        # except Exception as e: logger.error(f"Lambda invocation error: {e}"); return None
        # --- End Placeholder ---
        print("  - Placeholder: Lambda invocation logic not implemented.")
        return {"result": "simulated_lambda_success"}

    # --- EC2 Operations (Conceptual Placeholders) ---

    def start_ec2_instance(self, instance_id: str) -> bool:
        """Starts an EC2 instance."""
        logger.info(f"Starting EC2 instance '{instance_id}' (Conceptual)...")
        # Requires ec2:StartInstances permission
        # ec2_client = self._get_client('ec2')
        # if not ec2_client: return False
        # try: response = ec2_client.start_instances(InstanceIds=[instance_id]); return True
        # except ClientError as e: logger.error(...); return False
        print("  - Placeholder: EC2 start logic not implemented.")
        return True # Simulate success

    def stop_ec2_instance(self, instance_id: str) -> bool:
        """Stops an EC2 instance."""
        logger.info(f"Stopping EC2 instance '{instance_id}' (Conceptual)...")
        # Requires ec2:StopInstances permission
        # ec2_client = self._get_client('ec2')
        # if not ec2_client: return False
        # try: response = ec2_client.stop_instances(InstanceIds=[instance_id]); return True
        # except ClientError as e: logger.error(...); return False
        print("  - Placeholder: EC2 stop logic not implemented.")
        return True # Simulate success


    # --- Add methods for other services as needed ---
    # Example: Rekognition for image analysis
    # Example: Polly for text-to-speech
    # Example: SageMaker for ML model hosting/training


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- AWS Integration Example (Conceptual) ---")

    # Requires AWS credentials to be configured in the environment to actually run
    # (e.g., via environment variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
    # or an IAM role if run on AWS infrastructure.

    if not BOTO3_AVAILABLE:
        print("\nBoto3 library not found. Skipping AWS examples.")
    else:
        try:
            aws_integration = AWSIntegration(region_name="us-east-1") # Specify region or let boto3 find default

            # --- S3 Example ---
            # Replace with your actual bucket name and desired key/paths
            bucket = "your-devin-test-bucket-name" # <<< REPLACE
            local_file_to_upload = "temp_aws_upload_test.txt"
            s3_object_key = "test_files/my_upload.txt"
            local_download_path = "temp_aws_download.txt"

            print(f"\nAttempting S3 operations with bucket: {bucket}")
            print("NOTE: This requires the bucket to exist and appropriate IAM permissions.")

            # Create a dummy file to upload
            try:
                 with open(local_file_to_upload, "w") as f:
                     f.write(f"Hello from Devin AWS Integration test at {datetime.datetime.now()}")
            except IOError as e:
                 print(f"Could not create dummy file for upload: {e}")

            # Upload
            if os.path.exists(local_file_to_upload):
                upload_ok = aws_integration.upload_to_s3(bucket, s3_object_key, local_file_to_upload)
                print(f"Upload successful: {upload_ok}")

                if upload_ok:
                     # List
                     print("\nListing objects:")
                     obj_generator = aws_integration.list_s3_objects(bucket, prefix="test_files/")
                     found_objects = list(obj_generator) # Consume generator for example
                     for obj in found_objects:
                         print(f"  - Key: {obj['Key']}, Size: {obj['Size']}")
                     if not any(o['Key'] == s3_object_key for o in found_objects):
                         print(f"  - Warning: Uploaded object '{s3_object_key}' not found immediately in listing.")


                     # Download
                     download_ok = aws_integration.download_from_s3(bucket, s3_object_key, local_download_path)
                     print(f"\nDownload successful: {download_ok}")
                     if download_ok and os.path.exists(local_download_path):
                         print(f"  - Downloaded file content (first 100 chars):")
                         with open(local_download_path, 'r') as f: print(f"    '{f.read(100)}...'")
                         os.remove(local_download_path) # Clean up download

                # Clean up dummy upload file
                os.remove(local_file_to_upload)
            else:
                 print("Skipping List/Download because dummy upload file wasn't created/found.")


            # --- Other Service Examples (Conceptual Calls) ---
            print("\nInvoking conceptual Lambda function:")
            lambda_result = aws_integration.invoke_lambda("devin-processing-func", {"input_data": "test"})
            print(f"Lambda result: {lambda_result}")

            print("\nStarting/Stopping conceptual EC2 instance:")
            aws_integration.start_ec2_instance("i-0123456789abcdef0")
            aws_integration.stop_ec2_instance("i-0123456789abcdef0")

        except (NoCredentialsError, PartialCredentialsError):
             print("\nExample usage failed: AWS Credentials not found or incomplete.")
             print("Please configure AWS credentials (e.g., environment variables, ~/.aws/credentials, IAM role).")
        except Exception as e:
             print(f"\nAn unexpected error occurred during example usage: {e}")


    print("\n--- End Example ---")
