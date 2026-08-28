# Devin/cloud/azure_integration.py # Purpose: Provides integration support for Microsoft Azure services.

import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Generator

# Attempt to import Azure SDK libraries
try:
    from azure.identity import DefaultAzureCredential, CredentialUnavailableError
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, StorageStreamDownloader
    from azure.mgmt.compute import ComputeManagementClient # Example management client
    from azure.mgmt.resource import ResourceManagementClient # Example management client
    # from azure.functions import Out, HttpRequest # For interacting with Azure Functions triggers if needed
    # from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer # Example Cognitive Service
    from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError, HttpResponseError
    AZURE_LIBS_AVAILABLE = True
except ImportError:
    print("WARNING: Required 'azure-*' libraries not found (e.g., azure-identity, azure-storage-blob). AzureIntegration will use non-functional placeholders.")
    AZURE_LIBS_AVAILABLE = False
    # Define dummy exception classes if libs not installed
    class CredentialUnavailableError(Exception): pass
    class ResourceNotFoundError(Exception): pass
    class ClientAuthenticationError(Exception): pass
    class HttpResponseError(Exception): pass
    DefaultAzureCredential = None # type: ignore

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureIntegration:
    """
    Provides methods for interacting with various Microsoft Azure services.

    Handles initialization of Azure SDK clients using DefaultAzureCredential primarily.
    Includes basic error handling for common Azure exceptions.
    """

    def __init__(self, subscription_id: Optional[str] = None, credential: Optional[Any] = None):
        """
        Initializes the Azure Integration class.

        Args:
            subscription_id (Optional[str]): Your Azure Subscription ID. Required for many
                                            management plane operations. Can also be set via
                                            AZURE_SUBSCRIPTION_ID environment variable.
            credential (Optional[Any]): An Azure credential object (e.g., from azure.identity).
                                        Defaults to DefaultAzureCredential().
        """
        self.subscription_id = subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID")
        self._credential = None
        self._clients: Dict[str, Any] = {} # Cache for service clients

        if not AZURE_LIBS_AVAILABLE:
            logger.error("One or more azure-* libraries are not installed. Azure functionality unavailable.")
        else:
            try:
                # Initialize credential object
                self._credential = credential or DefaultAzureCredential()
                # Test credential availability (optional, will fail later if not configured)
                # token = self._credential.get_token("https://management.azure.com/.default") # Example scope
                # logger.info("Azure Credentials obtained successfully via DefaultAzureCredential.")
                logger.info(f"AzureIntegration initialized. Subscription ID: {self.subscription_id or 'Not Set (Needed for Mgmt)'}, Using DefaultAzureCredential: {credential is None}")
            except CredentialUnavailableError as e:
                logger.error(f"Azure Credential Error: {e}. Ensure credentials are configured (az login, env vars, Managed Identity).")
            except Exception as e:
                logger.error(f"Unexpected error initializing Azure Credentials: {e}")

    def _get_client(self, client_type: str, **kwargs) -> Optional[Any]:
        """Lazy-loads and returns an Azure SDK client."""
        if not AZURE_LIBS_AVAILABLE or self._credential is None:
            logger.error(f"Cannot get client for '{client_type}': Azure libs unavailable or credentials failed.")
            return None

        # Use kwargs to allow passing specific needs like endpoint URLs
        cache_key = f"{client_type}_{str(sorted(kwargs.items()))}" # Basic cache key

        if cache_key not in self._clients:
            try:
                logger.debug(f"Creating Azure client for type: {client_type} with kwargs: {kwargs}")
                if client_type == 'blob_service':
                    account_url = kwargs.get("account_url") # e.g., "https://<your_storage_account>.blob.core.windows.net"
                    if not account_url: raise ValueError("account_url kwarg is required for BlobServiceClient")
                    self._clients[cache_key] = BlobServiceClient(account_url=account_url, credential=self._credential)
                elif client_type == 'compute_mgmt':
                    if not self.subscription_id: raise ValueError("subscription_id required for ComputeManagementClient")
                    self._clients[cache_key] = ComputeManagementClient(credential=self._credential, subscription_id=self.subscription_id)
                elif client_type == 'resource_mgmt':
                     if not self.subscription_id: raise ValueError("subscription_id required for ResourceManagementClient")
                     self._clients[cache_key] = ResourceManagementClient(credential=self._credential, subscription_id=self.subscription_id)
                # Add other clients as needed (Functions, Cognitive Services, AI ML etc.)
                # elif client_type == 'speech':
                #     speech_key = os.environ.get("AZURE_SPEECH_KEY")
                #     speech_region = os.environ.get("AZURE_SPEECH_REGION")
                #     if not speech_key or not speech_region: raise ValueError("AZURE_SPEECH_KEY and AZURE_SPEECH_REGION required")
                #     speech_config = speech.SpeechConfig(subscription=speech_key, region=speech_region)
                #     self._clients[cache_key] = speech_config # Store config, synthesizer created on demand maybe
                else:
                    logger.error(f"Azure client type '{client_type}' not recognized in _get_client.")
                    return None
            except CredentialUnavailableError as e:
                 logger.error(f"Azure Credentials Error creating '{client_type}' client: {e}.")
                 return None
            except ValueError as e:
                 logger.error(f"Configuration error creating '{client_type}' client: {e}")
                 return None
            except Exception as e:
                logger.error(f"Failed to create Azure client for '{client_type}': {e}")
                return None
        return self._clients.get(cache_key)

    # --- Azure Blob Storage Operations ---

    def upload_to_blob(self, storage_account_url: str, container_name: str, blob_name: str, file_path: str) -> bool:
        """
        Uploads a local file to Azure Blob Storage.

        Args:
            storage_account_url (str): The URL of the storage account (e.g., "https://<account_name>.blob.core.windows.net").
            container_name (str): The name of the target container.
            blob_name (str): The desired name (path/filename) for the blob.
            file_path (str): The path to the local file to upload.

        Returns:
            bool: True if upload was successful, False otherwise.

        Requires: Storage Blob Data Contributor/Owner role on the container/storage account.
        """
        logger.info(f"Attempting to upload '{file_path}' to Azure Blob: {container_name}/{blob_name}")
        if not os.path.exists(file_path):
            logger.error(f"Upload failed: Local file not found at '{file_path}'")
            return False

        blob_service_client = self._get_client('blob_service', account_url=storage_account_url)
        if not blob_service_client: return False

        try:
            blob_client: BlobClient = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            logger.info(f"Successfully uploaded to Azure Blob: {container_name}/{blob_name}")
            return True
        except CredentialUnavailableError as e:
             logger.error(f"Upload failed: Azure Credentials Error: {e}")
             return False
        except ResourceNotFoundError:
             logger.error(f"Upload failed: Container '{container_name}' not found in account '{storage_account_url}'.")
             return False
        except ClientAuthenticationError as e:
              logger.error(f"Upload failed: Authentication error. Check credentials/permissions. Error: {e}")
              return False
        except HttpResponseError as e:
             logger.error(f"Upload failed: Azure HTTP Response Error: {e}")
             return False
        except Exception as e:
            logger.error(f"Upload failed: Unexpected error: {e}")
            return False

    def download_from_blob(self, storage_account_url: str, container_name: str, blob_name: str, download_path: str) -> bool:
        """
        Downloads a blob from Azure Blob Storage to a local file.

        Args:
            storage_account_url (str): URL of the storage account.
            container_name (str): The name of the source container.
            blob_name (str): The name (path/filename) of the blob.
            download_path (str): The local path where the file should be saved.

        Returns:
            bool: True if download was successful, False otherwise.

        Requires: Storage Blob Data Reader/Owner role on the blob/container/storage account.
        """
        logger.info(f"Attempting to download Azure Blob: {container_name}/{blob_name} to '{download_path}'")
        blob_service_client = self._get_client('blob_service', account_url=storage_account_url)
        if not blob_service_client: return False

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            blob_client: BlobClient = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            with open(download_path, "wb") as download_file:
                 stream: StorageStreamDownloader = blob_client.download_blob()
                 stream.readinto(download_file)
            logger.info(f"Successfully downloaded to '{download_path}'")
            return True
        except CredentialUnavailableError as e:
             logger.error(f"Download failed: Azure Credentials Error: {e}")
             return False
        except ResourceNotFoundError:
            logger.error(f"Download failed: Blob '{blob_name}' not found in container '{container_name}'.")
            return False
        except ClientAuthenticationError as e:
              logger.error(f"Download failed: Authentication error. Check credentials/permissions. Error: {e}")
              return False
        except HttpResponseError as e:
             logger.error(f"Download failed: Azure HTTP Response Error: {e}")
             return False
        except Exception as e:
            logger.error(f"Download failed: Unexpected error: {e}")
            return False

    def list_blobs(self, storage_account_url: str, container_name: str, name_starts_with: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Lists blobs in an Azure Blob Storage container.

        Args:
            storage_account_url (str): URL of the storage account.
            container_name (str): The name of the container.
            name_starts_with (Optional[str]): Optional prefix to filter blobs by.

        Yields:
            Dict[str, Any]: Dictionary containing information about each blob found
                           (e.g., name, size, last_modified).

        Requires: Storage Blob Data Reader/Owner or list permissions on the container.
        """
        logger.info(f"Listing blobs in Azure Container: {container_name}/{name_starts_with or ''}*")
        blob_service_client = self._get_client('blob_service', account_url=storage_account_url)
        if not blob_service_client: return

        try:
            container_client: ContainerClient = blob_service_client.get_container_client(container_name)
            blob_list = container_client.list_blobs(name_starts_with=name_starts_with)
            count = 0
            for blob in blob_list:
                 # Convert blob properties to a dict for consistent return type
                 yield {
                     'name': blob.name,
                     'size': blob.size,
                     'creation_time': blob.creation_time,
                     'last_modified': blob.last_modified,
                     'etag': blob.etag,
                     'content_type': blob.content_settings.content_type
                     # Add other properties as needed
                 }
                 count += 1
            logger.info(f"Found {count} blobs matching prefix.")
        except CredentialUnavailableError as e:
            logger.error(f"Listing failed: Azure Credentials Error: {e}")
        except ResourceNotFoundError:
             logger.error(f"Listing failed: Container '{container_name}' not found.")
        except ClientAuthenticationError as e:
              logger.error(f"Listing failed: Authentication error. Error: {e}")
              return False
        except HttpResponseError as e:
             logger.error(f"Listing failed: Azure HTTP Response Error: {e}")
        except Exception as e:
            logger.error(f"Listing failed: Unexpected error: {e}")


    # --- Other Azure Services (Conceptual Placeholders) ---

    def invoke_azure_function(self, function_app_url: str, data: Dict[str, Any], api_key: Optional[str] = None) -> Optional[Any]:
        """Invokes an Azure Function (HTTP trigger assumed)."""
        logger.info(f"Invoking Azure Function '{function_app_url}' (Conceptual)...")
        # Requires function-level authentication (e.g., function key, Azure AD)
        # Can use 'requests' library. Need to handle auth (e.g., x-functions-key header)
        # try:
        #     headers = {'Content-Type': 'application/json'}
        #     if api_key: headers['x-functions-key'] = api_key
        #     response = requests.post(function_app_url, json=data, headers=headers)
        #     response.raise_for_status()
        #     return response.json() # Or response.text
        # except Exception as e: logger.error(...); return None
        print("  - Placeholder: Azure Functions invocation logic not implemented.")
        return {"result": "simulated_azure_function_success"}

    def start_vm(self, resource_group_name: str, vm_name: str) -> bool:
        """Starts an Azure Virtual Machine."""
        logger.info(f"Starting Azure VM '{vm_name}' in group '{resource_group_name}' (Conceptual)...")
        # Requires Microsoft.Compute/virtualMachines/start/action permission
        # compute_client = self._get_client('compute_mgmt')
        # if not compute_client: return False
        # try:
        #     async_poller = compute_client.virtual_machines.begin_start(resource_group_name, vm_name)
        #     async_poller.result() # Wait for completion
        #     logger.info(f"VM '{vm_name}' started successfully.")
        #     return True
        # except Exception as e: logger.error(...); return False
        print("  - Placeholder: Azure VM start logic not implemented.")
        return True

    def stop_vm(self, resource_group_name: str, vm_name: str) -> bool:
        """Stops (deallocates) an Azure Virtual Machine."""
        logger.info(f"Stopping Azure VM '{vm_name}' in group '{resource_group_name}' (Conceptual)...")
        # Requires Microsoft.Compute/virtualMachines/deallocate/action permission
        # ... similar structure to start_vm using compute_client.virtual_machines.begin_deallocate ...
        print("  - Placeholder: Azure VM stop logic not implemented.")
        return True

    # Add methods for Azure ML, Cognitive Services (Vision, Speech, Language) as needed


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Azure Integration Example (Conceptual) ---")

    # Requires Azure credentials to be configured for DefaultAzureCredential to work
    # (e.g., run 'az login' locally, set environment variables AZURE_CLIENT_ID etc., use Managed Identity)

    if not AZURE_LIBS_AVAILABLE:
        print("\nAzure SDK libraries not found. Skipping Azure examples.")
    else:
        try:
            # subscription = os.environ.get("AZURE_SUBSCRIPTION_ID") # Ensure this is set if needed
            azure_integration = AzureIntegration() # Uses DefaultAzureCredential

            # --- Blob Storage Example ---
            # Replace with your actual storage account URL, container, etc.
            account_url = "https://yourdevinstorageacc.blob.core.windows.net" # <<< REPLACE
            container = "devin-test-container" # <<< REPLACE (must exist)
            local_file_to_upload = "temp_azure_upload_test.txt"
            blob_name = "test_data/azure_upload.txt"
            local_download_path = "temp_azure_download.txt"

            print(f"\nAttempting Azure Blob operations with container: {container}")
            print(f"NOTE: Requires container '{container}' to exist in account '{account_url}' and appropriate RBAC permissions.")

            # Create dummy file
            try:
                 with open(local_file_to_upload, "w") as f: f.write(f"Hello Azure from Devin @ {datetime.datetime.now()}")
            except IOError as e: print(f"Could not create dummy file: {e}")

            if os.path.exists(local_file_to_upload):
                 # Upload
                 upload_ok = azure_integration.upload_to_blob(account_url, container, blob_name, local_file_to_upload)
                 print(f"Upload successful: {upload_ok}")

                 if upload_ok:
                      # List
                      print("\nListing blobs:")
                      blob_generator = azure_integration.list_blobs(account_url, container, name_starts_with="test_data/")
                      found_blobs = list(blob_generator) # Consume generator
                      for blob_props in found_blobs:
                          print(f"  - Name: {blob_props['name']}, Size: {blob_props['size']}")
                      if not any(b['name'] == blob_name for b in found_blobs):
                           print(f"  - Warning: Uploaded blob '{blob_name}' not found immediately.")

                      # Download
                      download_ok = azure_integration.download_from_blob(account_url, container, blob_name, local_download_path)
                      print(f"\nDownload successful: {download_ok}")
                      if download_ok and os.path.exists(local_download_path):
                           print(f"  - Downloaded file content (first 100 chars):")
                           with open(local_download_path, 'r') as f: print(f"    '{f.read(100)}...'")
                           os.remove(local_download_path) # Clean up

                 # Clean up dummy upload file
                 os.remove(local_file_to_upload)
            else:
                 print("Skipping Blob List/Download because dummy upload file wasn't created/found.")

            # --- Other Service Examples (Conceptual Calls) ---
            print("\nInvoking conceptual Azure Function:")
            # func_url = "https://your-func-app.azurewebsites.net/api/myHttpTrigger" # Needs function key potentially
            # func_result = azure_integration.invoke_azure_function(func_url, {"name": "Devin"})
            # print(f"Azure Function result: {func_result}")

            print("\nStarting/Stopping conceptual Azure VM:")
            # resource_group = "my-devin-rg"
            # vm_name = "devin-worker-vm"
            # azure_integration.start_vm(resource_group, vm_name)
            # azure_integration.stop_vm(resource_group, vm_name)


        except CredentialUnavailableError as e:
             print("\nExample usage failed: Azure Credentials unavailable via DefaultAzureCredential.")
             print("Please configure Azure credentials (run 'az login', set environment variables, use Managed Identity, etc.).")
        except Exception as e:
             print(f"\nAn unexpected error occurred during example usage: {e}")

    print("\n--- End Example ---")
