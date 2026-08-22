# Devin/cloud/gcp_integration.py # Purpose: Provides integration support for Google Cloud Platform services.

import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Generator

# Attempt to import Google Cloud client libraries
try:
    from google.cloud import storage
    from google.cloud import compute_v1
    from google.cloud import functions_v1
    from google.cloud import aiplatform # Vertex AI
    from google.api_core import exceptions as google_exceptions
    from google.auth import exceptions as google_auth_exceptions
    GCP_LIBS_AVAILABLE = True
except ImportError:
    print("WARNING: Required 'google-cloud-*' libraries not found (e.g., google-cloud-storage). GCPIntegration will use non-functional placeholders.")
    GCP_LIBS_AVAILABLE = False
    # Define dummy exception classes if libs not installed
    class google_exceptions:
        class GoogleAPICallError(Exception): pass
        class NotFound(GoogleAPICallError): pass
        class Forbidden(GoogleAPICallError): pass
    class google_auth_exceptions:
        class DefaultCredentialsError(Exception): pass

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GCPIntegration:
    """
    Provides methods for interacting with various Google Cloud Platform services.

    Handles initialization of GCP client libraries and basic error handling.
    Relies on Application Default Credentials (ADC) for authentication primarily.
    """

    def __init__(self, project_id: Optional[str] = None, credentials: Optional[Any] = None):
        """
        Initializes the GCP Integration class.

        Args:
            project_id (Optional[str]): Your Google Cloud project ID. If None, the client libraries
                                        will attempt to infer it from the environment.
            credentials (Optional[Any]): A google.auth.credentials.Credentials object. If None,
                                         Application Default Credentials (ADC) are used.
        """
        self.project_id = project_id
        self.credentials = credentials
        self._clients: Dict[str, Any] = {} # Cache for service clients

        if not GCP_LIBS_AVAILABLE:
            logger.error("One or more google-cloud libraries are not installed. GCP functionality unavailable.")
        else:
             logger.info(f"GCPIntegration initialized. Project ID: {self.project_id or 'Default'}, Using ADC: {self.credentials is None}")
             # Could add a basic credential check here if desired, e.g., try creating storage client

    def _get_client(self, service_name: str) -> Optional[Any]:
        """Lazy-loads and returns a GCP client for a given service."""
        if not GCP_LIBS_AVAILABLE:
            logger.error(f"Cannot get client for '{service_name}': google-cloud libraries unavailable.")
            return None

        if service_name not in self._clients:
            try:
                logger.debug(f"Creating GCP client for service: {service_name}")
                if service_name == 'storage':
                    self._clients['storage'] = storage.Client(project=self.project_id, credentials=self.credentials)
                elif service_name == 'compute':
                     self._clients['compute'] = compute_v1.InstancesClient(credentials=self.credentials)
                elif service_name == 'functions':
                     self._clients['functions'] = functions_v1.CloudFunctionsServiceClient(credentials=self.credentials)
                elif service_name == 'aiplatform':
                     # AI Platform (Vertex AI) often needs project and location
                     location = os.environ.get("GCP_REGION", "us-central1") # Example default location
                     aiplatform.init(project=self.project_id, location=location, credentials=self.credentials)
                     self._clients['aiplatform'] = aiplatform # Store the module itself or specific clients
                # Add other clients as needed (Vision, Speech, etc.)
                else:
                     logger.error(f"GCP client type '{service_name}' not recognized in _get_client.")
                     return None
            except google_auth_exceptions.DefaultCredentialsError as e:
                 logger.error(f"GCP Default Credentials Error creating '{service_name}' client: {e}. Ensure ADC is configured (run 'gcloud auth application-default login' or set GOOGLE_APPLICATION_CREDENTIALS).")
                 return None
            except Exception as e:
                logger.error(f"Failed to create GCP client for '{service_name}': {e}")
                return None
        return self._clients.get(service_name)

    # --- Google Cloud Storage (GCS) Operations ---

    def upload_to_gcs(self, bucket_name: str, blob_name: str, file_path: str) -> bool:
        """
        Uploads a local file to a Google Cloud Storage bucket.

        Args:
            bucket_name (str): The name of the target GCS bucket.
            blob_name (str): The desired name (path/filename) for the object (blob) in the bucket.
            file_path (str): The path to the local file to upload.

        Returns:
            bool: True if upload was successful, False otherwise.

        Requires: roles/storage.objectCreator or roles/storage.objectAdmin IAM permission on the bucket.
        """
        logger.info(f"Attempting to upload '{file_path}' to gs://{bucket_name}/{blob_name}")
        if not os.path.exists(file_path):
            logger.error(f"Upload failed: Local file not found at '{file_path}'")
            return False

        storage_client = self._get_client('storage')
        if not storage_client: return False

        try:
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            logger.info(f"Successfully uploaded to gs://{bucket_name}/{blob_name}")
            return True
        except google_auth_exceptions.DefaultCredentialsError as e:
             logger.error(f"Upload failed: GCP Credentials Error: {e}")
             return False
        except google_exceptions.NotFound:
             logger.error(f"Upload failed: Bucket '{bucket_name}' not found.")
             return False
        except google_exceptions.Forbidden as e:
             logger.error(f"Upload failed: Permission denied for bucket '{bucket_name}'. Check IAM roles. Error: {e}")
             return False
        except Exception as e:
            logger.error(f"Upload failed: Unexpected error: {e}")
            return False

    def download_from_gcs(self, bucket_name: str, blob_name: str, download_path: str) -> bool:
        """
        Downloads an object (blob) from a GCS bucket to a local file.

        Args:
            bucket_name (str): The name of the source GCS bucket.
            blob_name (str): The name (path/filename) of the blob within the bucket.
            download_path (str): The local path where the file should be saved.

        Returns:
            bool: True if download was successful, False otherwise.

        Requires: roles/storage.objectViewer IAM permission on the object/bucket.
        """
        logger.info(f"Attempting to download gs://{bucket_name}/{blob_name} to '{download_path}'")
        storage_client = self._get_client('storage')
        if not storage_client: return False

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.download_to_filename(download_path)
            logger.info(f"Successfully downloaded to '{download_path}'")
            return True
        except google_auth_exceptions.DefaultCredentialsError as e:
             logger.error(f"Download failed: GCP Credentials Error: {e}")
             return False
        except google_exceptions.NotFound:
            logger.error(f"Download failed: Object '{blob_name}' not found in bucket '{bucket_name}'.")
            return False
        except google_exceptions.Forbidden as e:
             logger.error(f"Download failed: Permission denied for object '{blob_name}'. Error: {e}")
             return False
        except Exception as e:
            logger.error(f"Download failed: Unexpected error: {e}")
            return False

    def list_gcs_blobs(self, bucket_name: str, prefix: Optional[str] = None) -> Generator[storage.Blob, None, None]:
        """
        Lists blobs in a GCS bucket, optionally filtered by prefix.

        Args:
            bucket_name (str): The name of the GCS bucket.
            prefix (Optional[str]): Optional prefix to filter blobs by.

        Yields:
            storage.Blob: Blob object containing metadata (name, size, updated, etc.).

        Requires: roles/storage.objectViewer or roles/storage.objectLister IAM permission on the bucket.
        """
        logger.info(f"Listing objects in gs://{bucket_name}/{prefix or ''}*")
        storage_client = self._get_client('storage')
        if not storage_client: return

        try:
            blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
            count = 0
            for blob in blobs:
                yield blob
                count += 1
            logger.info(f"Found {count} blobs matching prefix.")
        except google_auth_exceptions.DefaultCredentialsError as e:
            logger.error(f"Listing failed: GCP Credentials Error: {e}")
        except google_exceptions.NotFound:
             logger.error(f"Listing failed: Bucket '{bucket_name}' not found.")
        except google_exceptions.Forbidden as e:
             logger.error(f"Listing failed: Permission denied for bucket '{bucket_name}'. Error: {e}")
        except Exception as e:
            logger.error(f"Listing failed: Unexpected error: {e}")


    # --- Other GCP Services (Conceptual Placeholders) ---

    def invoke_cloud_function(self, function_url_or_name: str, data: Dict[str, Any]) -> Optional[Any]:
        """Invokes a Google Cloud Function (HTTP trigger assumed)."""
        logger.info(f"Invoking Cloud Function '{function_url_or_name}' (Conceptual)...")
        # Requires roles/cloudfunctions.invoker permission
        # functions_client = self._get_client('functions') # Or use requests for HTTP trigger URL
        # if not functions_client: return None
        # try:
        #    # If using client library for non-HTTP function:
        #    # response = functions_client.call_function(name=function_name_resource, data=json.dumps(data))
        #    # result = json.loads(response.result)
        #    # If using requests for HTTP trigger:
        #    # headers = {'Authorization': f'bearer {get_id_token(function_url_or_name)}'} # Need auth helper
        #    # response = requests.post(function_url_or_name, json=data, headers=headers)
        #    # response.raise_for_status()
        #    # return response.json()
        # except Exception as e: logger.error(...) return None
        print("  - Placeholder: Cloud Functions invocation logic not implemented.")
        return {"result": "simulated_cloud_function_success"}

    def start_gce_instance(self, instance_name: str, zone: Optional[str] = None) -> bool:
        """Starts a Google Compute Engine instance."""
        logger.info(f"Starting GCE instance '{instance_name}' in zone '{zone}' (Conceptual)...")
        # Requires roles/compute.instanceAdmin.v1 permission
        # compute_client = self._get_client('compute')
        # if not compute_client: return False
        # try:
        #    project = self.project_id or get_default_project() # Need helper
        #    zone = zone or get_default_zone() # Need helper
        #    operation = compute_client.start(project=project, zone=zone, instance=instance_name)
        #    # Wait for operation completion if needed
        #    return True
        # except Exception as e: logger.error(...); return False
        print("  - Placeholder: GCE start logic not implemented.")
        return True

    def stop_gce_instance(self, instance_name: str, zone: Optional[str] = None) -> bool:
        """Stops a Google Compute Engine instance."""
        logger.info(f"Stopping GCE instance '{instance_name}' in zone '{zone}' (Conceptual)...")
        # Requires roles/compute.instanceAdmin.v1 permission
        # ... similar structure to start_gce_instance using compute_client.stop ...
        print("  - Placeholder: GCE stop logic not implemented.")
        return True

    def predict_vertex_ai(self, endpoint_id: str, instances: List[Any]) -> Optional[List[Any]]:
         """Sends a prediction request to a Vertex AI Endpoint."""
         logger.info(f"Sending prediction to Vertex AI Endpoint '{endpoint_id}' (Conceptual)...")
         # Requires roles/aiplatform.user permission
         # aiplatform_client = self._get_client('aiplatform') # Needs location init
         # if not aiplatform_client: return None
         # try:
         #     endpoint = aiplatform.Endpoint(endpoint_name=endpoint_id) # Use endpoint ID or full name
         #     prediction = endpoint.predict(instances=instances)
         #     return prediction.predictions
         # except Exception as e: logger.error(...); return None
         print("  - Placeholder: Vertex AI prediction logic not implemented.")
         return [{"prediction": "mock_vertex_prediction"}]


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- GCP Integration Example (Conceptual) ---")

    # Requires GCP credentials to be configured via ADC for actual execution
    # (e.g., run 'gcloud auth application-default login' locally, or run on GCP infra)

    if not GCP_LIBS_AVAILABLE:
        print("\nGoogle Cloud libraries not found. Skipping GCP examples.")
    else:
        try:
            # project = "your-gcp-project-id" # Optional: Explicitly set project ID
            gcp_integration = GCPIntegration() # Uses ADC

            # --- GCS Example ---
            # Replace with your actual bucket name and desired key/paths
            bucket = "your-devin-gcs-test-bucket" # <<< REPLACE
            local_file_to_upload = "temp_gcp_upload_test.txt"
            gcs_blob_name = "test_files/my_gcp_upload.txt"
            local_download_path = "temp_gcp_download.txt"

            print(f"\nAttempting GCS operations with bucket: {bucket}")
            print("NOTE: This requires the bucket to exist and appropriate IAM permissions via ADC.")

            # Create a dummy file to upload
            try:
                 with open(local_file_to_upload, "w") as f:
                     f.write(f"Hello from Devin GCP Integration test at {datetime.datetime.now()}")
            except IOError as e:
                 print(f"Could not create dummy file for upload: {e}")


            if os.path.exists(local_file_to_upload):
                upload_ok = gcp_integration.upload_to_gcs(bucket, gcs_blob_name, local_file_to_upload)
                print(f"Upload successful: {upload_ok}")

                if upload_ok:
                     # List
                     print("\nListing objects:")
                     blob_generator = gcp_integration.list_gcs_blobs(bucket, prefix="test_files/")
                     found_blobs = list(blob_generator) # Consume generator
                     for blob in found_blobs:
                         print(f"  - Name: {blob.name}, Size: {blob.size}, Updated: {blob.updated}")
                     if not any(b.name == gcs_blob_name for b in found_blobs):
                          print(f"  - Warning: Uploaded blob '{gcs_blob_name}' not found immediately in listing.")

                     # Download
                     download_ok = gcp_integration.download_from_gcs(bucket, gcs_blob_name, local_download_path)
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
            print("\nInvoking conceptual Cloud Function:")
            cf_result = gcp_integration.invoke_cloud_function("https://your-region-your-project.cloudfunctions.net/my-function", {"input": "test"})
            print(f"Cloud Function result: {cf_result}")

            print("\nStarting/Stopping conceptual GCE instance:")
            gcp_integration.start_gce_instance("devin-worker-instance", zone="us-central1-a")
            gcp_integration.stop_gce_instance("devin-worker-instance", zone="us-central1-a")

            print("\nGetting conceptual Vertex AI prediction:")
            # endpoint_id = "projects/YOUR_PROJECT/locations/us-central1/endpoints/YOUR_ENDPOINT_ID" # Example
            # instances = [{"feature1": 1.0, "feature2": 2.0}, {"feature1": 3.0, "feature2": 4.0}]
            # vertex_preds = gcp_integration.predict_vertex_ai(endpoint_id, instances)
            # print(f"Vertex AI predictions: {vertex_preds}")


        except google_auth_exceptions.DefaultCredentialsError as e:
             print("\nExample usage failed: GCP Default Credentials not found or invalid.")
             print("Please configure ADC (run 'gcloud auth application-default login' or set GOOGLE_APPLICATION_CREDENTIALS).")
        except Exception as e:
             print(f"\nAn unexpected error occurred during example usage: {e}")


    print("\n--- End Example ---")
