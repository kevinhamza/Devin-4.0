# # Devin/modules/cloud_tools.py
# # Purpose: Provides low-level, provider-specific tools for direct interaction
# #          with cloud resources (AWS, GCP, Azure).
# # Cloud resource management ☁️🔧

# import logging
# import time
# import random
# import uuid
# from typing import List, Dict, Any, Optional

# # Configure basic logging
# logger = logging.getLogger("CloudTools")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class AWSTools:
#     """
#     Provides a conceptual toolbox for interacting with Amazon Web Services (AWS).
#     In a real system, this would be a wrapper around the 'boto3' Python SDK.
#     """
#     def __init__(self,
#                  aws_access_key_id_placeholder: Optional[str] = None,
#                  aws_secret_access_key_placeholder: Optional[str] = None,
#                  region_name: str = "us-east-1"):
#         """
#         Initializes the AWS tools with conceptual credentials.
#         """
#         self.region_name = region_name
#         self.credentials = {
#             "aws_access_key_id": aws_access_key_id_placeholder,
#             "aws_secret_access_key": aws_secret_access_key_placeholder
#         }
#         logger.info(f"AWSTools initialized for region '{self.region_name}'. Conceptually using Boto3.")
#         logger.warning("All AWS operations are conceptual and do not represent real API calls.")

#     def _get_client_conceptual(self, service_name: str, region: Optional[str] = None) -> str:
#         """Simulates creating a boto3 client."""
#         target_region = region or self.region_name
#         return f"boto3.client('{service_name}', region_name='{target_region}')"

#     # --- EC2 (Virtual Machines) ---
#     def ec2_describe_instances(self, instance_ids: Optional[List[str]] = None, region: Optional[str] = None) -> Dict[str, Any]:
#         """
#         Conceptually describes EC2 instances.
#         Real-world equivalent: `boto3.client('ec2').describe_instances()`
#         """
#         client = self._get_client_conceptual("ec2", region)
#         filters = f" with filters for IDs: {instance_ids}" if instance_ids else ""
#         logger.info(f"CONCEPTUAL BOTO3: Using {client}.describe_instances(){filters}")
        
#         # Simulate a response structure similar to boto3
#         simulated_instances = []
#         for i in range(random.randint(1, 3)):
#             instance_id = f"i-{uuid.uuid4().hex[:17]}"
#             simulated_instances.append({
#                 "InstanceId": instance_id,
#                 "ImageId": "ami-0c55b159cbfafe1f0",
#                 "InstanceType": "t2.micro",
#                 "State": {"Name": random.choice(["running", "stopped"])},
#                 "PrivateIpAddress": f"172.31.{random.randint(0,255)}.{random.randint(0,255)}",
#                 "PublicIpAddress": f"54.{random.randint(100,200)}.{random.randint(0,255)}.{random.randint(0,255)}",
#                 "Tags": [{"Key": "Name", "Value": f"WebServer_{i+1}"}]
#             })
        
#         return {"Reservations": [{"Instances": simulated_instances}]}

#     def ec2_run_instances(self, image_id: str, instance_type: str, count: int, key_name: str, security_group_ids: List[str], region: Optional[str] = None) -> Dict[str, Any]:
#         """Conceptually launches new EC2 instances."""
#         client = self._get_client_conceptual("ec2", region)
#         logger.info(f"CONCEPTUAL BOTO3: Using {client}.run_instances(ImageId='{image_id}', InstanceType='{instance_type}', MinCount=1, MaxCount={count}, ...)")
#         instance_id = f"i-{uuid.uuid4().hex[:17]}"
#         logger.info(f"  Successfully launched conceptual instance with ID: {instance_id}")
#         return {"Instances": [{"InstanceId": instance_id, "State": {"Name": "pending"}}]}

#     def ec2_stop_instances(self, instance_ids: List[str], region: Optional[str] = None) -> Dict[str, Any]:
#         """Conceptually stops EC2 instances."""
#         client = self._get_client_conceptual("ec2", region)
#         logger.info(f"CONCEPTUAL BOTO3: Using {client}.stop_instances(InstanceIds={instance_ids})")
#         return {"StoppingInstances": [{"InstanceId": i, "CurrentState": {"Name": "stopping"}} for i in instance_ids]}

#     # --- S3 (Object Storage) ---
#     def s3_list_buckets(self) -> Dict[str, Any]:
#         """Conceptually lists all S3 buckets."""
#         client = self._get_client_conceptual("s3")
#         logger.info(f"CONCEPTUAL BOTO3: Using {client}.list_buckets()")
#         buckets = []
#         for i in range(random.randint(2, 5)):
#             buckets.append({
#                 "Name": f"my-unique-bucket-name-{uuid.uuid4().hex[:8]}",
#                 "CreationDate": "simulated_datetime_object"
#             })
#         return {"Buckets": buckets, "Owner": {"DisplayName": "devin_user"}}

#     def s3_list_objects(self, bucket_name: str, prefix: Optional[str] = None) -> Dict[str, Any]:
#         """Conceptually lists objects in an S3 bucket."""
#         client = self._get_client_conceptual("s3")
#         logger.info(f"CONCEPTUAL BOTO3: Using {client}.list_objects_v2(Bucket='{bucket_name}', Prefix='{prefix or ''}')")
#         contents = []
#         for i in range(random.randint(1, 10)):
#             contents.append({
#                 "Key": f"{prefix or 'logs'}/log_{i+1}.txt",
#                 "LastModified": "simulated_datetime",
#                 "Size": random.randint(100, 50000),
#                 "StorageClass": "STANDARD"
#             })
#         return {"Contents": contents}

#     def s3_get_bucket_policy_status(self, bucket_name: str) -> Dict[str, Any]:
#         """Conceptually checks if a bucket is public."""
#         client = self._get_client_conceptual("s3")
#         logger.info(f"CONCEPTUAL BOTO3: Using {client}.get_public_access_block() and {client}.get_bucket_policy_status()")
#         is_public = random.choice([True, False, False, False]) # 25% chance of being public
#         return {"PolicyStatus": {"IsPublic": is_public}}

#     # --- IAM (Identity and Access Management) ---
#     def iam_list_users(self) -> Dict[str, Any]:
#         """Conceptually lists IAM users."""
#         client = self._get_client_conceptual("iam")
#         logger.info(f"CONCEPTUAL BOTO3: Using {client}.list_users()")
#         users = []
#         for name in ["devin_user", "admin", "service_account_ci", "test_user"]:
#             users.append({
#                 "UserName": name,
#                 "UserId": f"AIDA{uuid.uuid4().hex.upper()[:17]}",
#                 "Arn": f"arn:aws:iam::123456789012:user/{name}"
#             })
#         return {"Users": users}

#     def iam_get_user_policy(self, user_name: str, policy_name: str) -> Dict[str, Any]:
#         """Conceptually gets a specific IAM policy for a user."""
#         client = self._get_client_conceptual("iam")
#         logger.info(f"CONCEPTUAL BOTO3: Using {client}.get_user_policy(UserName='{user_name}', PolicyName='{policy_name}')")
#         # Simulate a policy document
#         policy_document = {
#             "Version": "2012-10-17",
#             "Statement": [{
#                 "Effect": "Allow",
#                 "Action": ["s3:GetObject", "s3:ListBucket"],
#                 "Resource": f"arn:aws:s3:::my-unique-bucket-name-*"
#             }]
#         }
#         return {"UserName": user_name, "PolicyName": policy_name, "PolicyDocument": policy_document}

#     # --- RDS (Relational Database Service) ---
#     def rds_describe_db_instances(self, db_instance_identifier: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
#         """Conceptually describes RDS database instances."""
#         client = self._get_client_conceptual("rds", region)
#         logger.info(f"CONCEPTUAL BOTO3: Using {client}.describe_db_instances(DBInstanceIdentifier='{db_instance_identifier or 'all'}')")
#         db_instances = []
#         for i in range(random.randint(1, 2)):
#             db_instances.append({
#                 "DBInstanceIdentifier": f"database-{i+1}",
#                 "DBInstanceClass": "db.t3.medium",
#                 "Engine": random.choice(["postgres", "mysql"]),
#                 "DBInstanceStatus": "available",
#                 "Endpoint": {
#                     "Address": f"database-{i+1}.{uuid.uuid4().hex[:12]}.{region or self.region_name}.rds.amazonaws.com",
#                     "Port": random.choice([5432, 3306])
#                 },
#                 "MultiAZ": random.choice([True, False])
#             })
#         return {"DBInstances": db_instances}

# import logging # Already imported in Part 1
# import time # Already imported in Part 1
# import random # Already imported in Part 1
# import uuid # Already imported in Part 1
# from typing import List, Dict, Any, Optional # Already imported in Part 1

# class GCPTools:
#     """
#     Provides a conceptual toolbox for interacting with Google Cloud Platform (GCP).
#     In a real system, this would be a wrapper around the 'google-cloud-python' SDKs.
#     """
#     def __init__(self,
#                  project_id_placeholder: str,
#                  gcp_credentials_path_placeholder: Optional[str] = None):
#         """
#         Initializes the GCP tools with a conceptual project ID and credentials path.
#         """
#         self.project_id = project_id_placeholder
#         self.credentials_path = gcp_credentials_path_placeholder
#         logger.info(f"GCPTools initialized for project '{self.project_id}'. Conceptually using google-cloud-python SDKs.")
#         logger.warning("All GCP operations are conceptual and do not represent real API calls.")

#     def _get_client_conceptual(self, service_name: str) -> str:
#         """Simulates creating a google-cloud-python client."""
#         # e.g., 'compute_v1', 'storage', 'iam'
#         return f"google.cloud.{service_name}.Client(project='{self.project_id}')"

#     # --- Compute Engine (Virtual Machines) ---
#     def compute_instances_list(self, zone: str) -> Dict[str, Any]:
#         """
#         Conceptually lists all VM instances in a given zone.
#         Real-world equivalent: `compute_v1.InstancesClient().list()`
#         """
#         client = self._get_client_conceptual("compute_v1.InstancesClient")
#         logger.info(f"CONCEPTUAL GCP SDK: Using {client}.list(project='{self.project_id}', zone='{zone}')")
        
#         # Simulate a response structure similar to the GCP SDK
#         simulated_items = []
#         for i in range(random.randint(1, 2)):
#             instance_id = str(random.randint(10**18, 10**19-1))
#             instance_name = f"gce-instance-{i+1}"
#             simulated_items.append({
#                 "id": instance_id,
#                 "name": instance_name,
#                 "machineType": f"zones/{zone}/machineTypes/e2-medium",
#                 "status": "RUNNING",
#                 "networkInterfaces": [{
#                     "networkIP": f"10.128.0.{random.randint(2,10)}",
#                     "accessConfigs": [{
#                         "natIP": f"34.{random.randint(60,80)}.{random.randint(0,255)}.{random.randint(0,255)}"
#                     }]
#                 }],
#                 "tags": {"items": ["web-server", "dev-env"]}
#             })
#         return {"items": simulated_items}

#     # --- Cloud Storage (Buckets) ---
#     def storage_buckets_list(self) -> Dict[str, Any]:
#         """
#         Conceptually lists all Cloud Storage buckets in the project.
#         Real-world equivalent: `storage.Client().list_buckets()`
#         """
#         client = self._get_client_conceptual("storage")
#         logger.info(f"CONCEPTUAL GCP SDK: Using {client}.list_buckets()")
#         buckets = []
#         for i in range(random.randint(2, 4)):
#             buckets.append({
#                 "kind": "storage#bucket",
#                 "id": f"my-gcp-project-bucket-{uuid.uuid4().hex[:8]}",
#                 "name": f"my-gcp-project-bucket-{uuid.uuid4().hex[:8]}",
#                 "location": random.choice(["US-CENTRAL1", "EUROPE-WEST1"])
#             })
#         return {"items": buckets}

#     # --- IAM (Identity and Access Management) ---
#     def iam_service_accounts_list(self) -> Dict[str, Any]:
#         """
#         Conceptually lists IAM service accounts in the project.
#         Real-world equivalent: `iam_v1.ServiceAccountsClient().list_service_accounts()`
#         """
#         client = self._get_client_conceptual("iam_v1.ServiceAccountsClient")
#         logger.info(f"CONCEPTUAL GCP SDK: Using {client}.list_service_accounts(name='projects/{self.project_id}')")
#         accounts = []
#         for name in ["compute-engine-default", "app-engine-default", "custom-ci-cd-runner"]:
#             accounts.append({
#                 "name": f"projects/{self.project_id}/serviceAccounts/{name}@{self.project_id}.iam.gserviceaccount.com",
#                 "projectId": self.project_id,
#                 "displayName": name.replace('-', ' ').title(),
#                 "email": f"{name}@{self.project_id}.iam.gserviceaccount.com"
#             })
#         return {"accounts": accounts}


# class AzureTools:
#     """
#     Provides a conceptual toolbox for interacting with Microsoft Azure.
#     In a real system, this would be a wrapper around the 'azure-sdk-for-python' libraries.
#     """
#     def __init__(self,
#                  subscription_id_placeholder: str,
#                  azure_credentials_placeholder: Optional[Any] = None):
#         """
#         Initializes the Azure tools with a conceptual subscription ID and credentials.
#         """
#         self.subscription_id = subscription_id_placeholder
#         self.credentials = azure_credentials_placeholder # Could be a ServicePrincipalCredentials object
#         logger.info(f"AzureTools initialized for subscription '{self.subscription_id}'. Conceptually using azure-sdk-for-python.")
#         logger.warning("All Azure operations are conceptual and do not represent real API calls.")

#     def _get_client_conceptual(self, client_class_name: str) -> str:
#         """Simulates creating an azure-sdk-for-python client."""
#         # e.g., 'ComputeManagementClient', 'StorageManagementClient', 'ResourceManagementClient'
#         return f"{client_class_name}(credentials=conceptual_creds, subscription_id='{self.subscription_id}')"

#     # --- Virtual Machines ---
#     def vm_list(self, resource_group_name: str) -> List[Dict[str, Any]]:
#         """
#         Conceptually lists all Virtual Machines in a given resource group.
#         Real-world equivalent: `ComputeManagementClient.virtual_machines.list()`
#         """
#         client = self._get_client_conceptual("ComputeManagementClient")
#         logger.info(f"CONCEPTUAL AZURE SDK: Using {client}.virtual_machines.list(resource_group_name='{resource_group_name}')")

#         simulated_vms = []
#         for i in range(random.randint(1, 2)):
#             vm_name = f"azure-vm-{i+1}"
#             simulated_vms.append({
#                 "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/{vm_name}",
#                 "name": vm_name,
#                 "type": "Microsoft.Compute/virtualMachines",
#                 "location": "eastus",
#                 "properties": {
#                     "hardwareProfile": {"vmSize": "Standard_DS1_v2"},
#                     "osProfile": {"computerName": vm_name, "adminUsername": "azureuser"},
#                     "provisioningState": "Succeeded"
#                 }
#             })
#         return simulated_vms

#     # --- Storage (Containers in Storage Accounts) ---
#     def storage_account_list_containers(self, resource_group_name: str, account_name: str) -> List[Dict[str, Any]]:
#         """
#         Conceptually lists blob containers within a storage account.
#         Real-world equivalent: `BlobServiceClient.list_containers()`
#         """
#         # Note: Interacting with data (blobs, containers) uses a different client than managing the storage account itself.
#         client = self._get_client_conceptual("BlobServiceClient")
#         logger.info(f"CONCEPTUAL AZURE SDK: Using {client}.list_containers() for account '{account_name}'")
#         containers = []
#         for name in ["logs", "backups", "data-payloads"]:
#             containers.append({
#                 "name": name,
#                 "properties": {
#                     "last_modified": "simulated_datetime",
#                     "lease_status": "unlocked",
#                     "public_access": random.choice(["blob", None])
#                 }
#             })
#         return containers

#     # --- Azure Active Directory (Entra ID) / Users ---
#     def ad_user_get(self, user_principal_name: str) -> Optional[Dict[str, Any]]:
#         """
#         Conceptually gets a user from Azure AD (now Entra ID).
#         Real-world equivalent: `GraphRbacManagementClient.users.get()` or Microsoft Graph API call.
#         """
#         client = self._get_client_conceptual("GraphRbacManagementClient")
#         logger.info(f"CONCEPTUAL AZURE SDK: Using {client}.users.get(upn='{user_principal_name}')")
        
#         if "devin" in user_principal_name:
#             return {
#                 "objectType": "User",
#                 "userPrincipalName": user_principal_name,
#                 "displayName": "Devin AI User",
#                 "mail": user_principal_name,
#                 "accountEnabled": True
#             }
#         return None

# # Devin/modules/cloud_tools.py
# # (Continuation - Requires Part 1 and 2 for AWSTools, GCPTools, and AzureTools classes)
# # Purpose: Provides low-level, provider-specific tools for direct interaction
# #          with cloud resources (AWS, GCP, Azure).
# # Cloud resource management ☁️🔧

# import logging # Already imported in Part 1
# import json # Imported for this part for pretty printing
# import random # Already imported in Part 1
# import uuid # Already imported in Part 1
# from typing import List, Dict, Any, Optional # Already imported in Part 1

# # --- Example Usage Tying All Toolsets Together ---
# if __name__ == "__main__":
#     print("================================================================")
#     print("=== Cloud Tools Module Prototype (Provider-Specific Demos) ☁️🔧 ===")
#     print("================================================================")

#     # Use a helper for pretty printing JSON-like dictionary outputs
#     def pretty_print_dict(data: Any):
#         print(json.dumps(data, indent=2, default=str))


#     # --- 1. AWS Tools Demonstration ---
#     print("\n---------- AWS Tools Demo ----------")
#     # Initialize the AWS toolbox
#     aws_tools = AWSTools(
#         aws_access_key_id_placeholder="CONCEPTUAL_AKIA...",
#         aws_secret_access_key_placeholder="CONCEPTUAL_SECRET...",
#         region_name="us-west-2"
#     )

#     # Use a tool to describe EC2 instances
#     print("\n[AWS] Describing EC2 Instances...")
#     ec2_instances_response = aws_tools.ec2_describe_instances()
#     pretty_print_dict(ec2_instances_response)

#     # Use a tool to list S3 buckets
#     print("\n[AWS] Listing S3 Buckets...")
#     s3_buckets_response = aws_tools.s3_list_buckets()
#     pretty_print_dict(s3_buckets_response)

#     # Use a tool to describe RDS instances
#     print("\n[AWS] Describing RDS DB Instances...")
#     rds_instances_response = aws_tools.rds_describe_db_instances(region="us-west-2")
#     pretty_print_dict(rds_instances_response)


#     # --- 2. GCP Tools Demonstration ---
#     print("\n\n---------- GCP Tools Demo ----------")
#     # Initialize the GCP toolbox
#     gcp_tools = GCPTools(
#         project_id_placeholder="devin-ai-project-123456",
#         gcp_credentials_path_placeholder="/path/to/conceptual/gcp_creds.json"
#     )

#     # Use a tool to list Compute Engine instances
#     print("\n[GCP] Listing Compute Engine Instances in zone 'us-central1-a'...")
#     gce_instances_response = gcp_tools.compute_instances_list(zone="us-central1-a")
#     pretty_print_dict(gce_instances_response)

#     # Use a tool to list IAM Service Accounts
#     print("\n[GCP] Listing IAM Service Accounts...")
#     iam_sa_response = gcp_tools.iam_service_accounts_list()
#     pretty_print_dict(iam_sa_response)


#     # --- 3. Azure Tools Demonstration ---
#     print("\n\n---------- Azure Tools Demo ----------")
#     # Initialize the Azure toolbox
#     azure_tools = AzureTools(
#         subscription_id_placeholder=str(uuid.uuid4()), # Generate a conceptual UUID for subscription ID
#         azure_credentials_placeholder="ConceptualServicePrincipalCredentials"
#     )
    
#     # Define conceptual resource group for the demo
#     azure_rg = "Devin-Resource-Group"

#     # Use a tool to list Virtual Machines in a resource group
#     print(f"\n[Azure] Listing Virtual Machines in Resource Group '{azure_rg}'...")
#     azure_vms_response = azure_tools.vm_list(resource_group_name=azure_rg)
#     pretty_print_dict(azure_vms_response)
    
#     # Use a tool to list Storage Containers in a storage account
#     azure_sa = "devinstorageaccount123"
#     print(f"\n[Azure] Listing Storage Containers in Account '{azure_sa}'...")
#     azure_containers_response = azure_tools.storage_account_list_containers(
#         resource_group_name=azure_rg,
#         account_name=azure_sa
#     )
#     pretty_print_dict(azure_containers_response)


#     print("\n================================================================")
#     print("=== Cloud Tools Module Prototype Complete ===")
#     print("================================================================")



# Devin/modules/cloud_tools.py
# Purpose: Provides a functional, low-level, provider-specific toolkit for
#          direct interaction with cloud resources (AWS, GCP, Azure).

import logging
from typing import List, Dict, Any, Optional

# --- Provider-specific SDKs ---
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_SDK_AVAILABLE = True
except ImportError:
    AWS_SDK_AVAILABLE = False

try:
    from google.cloud import compute_v1, storage
    from google.api_core import exceptions as gcp_exceptions
    GCP_SDK_AVAILABLE = True
except ImportError:
    GCP_SDK_AVAILABLE = False

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("CloudTools")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class AWSTools:
    """A functional toolbox for interacting with Amazon Web Services using boto3."""
    def __init__(self, region_name: str = "us-east-1"):
        if not AWS_SDK_AVAILABLE:
            raise ImportError("AWS SDK (boto3) is required. 'pip install boto3'")
        try:
            self.session = boto3.Session(region_name=region_name)
            self.ec2 = self.session.client('ec2')
            self.s3 = self.session.client('s3')
            # Verify credentials by making a simple, low-cost call
            self.ec2.describe_regions()
            logger.info(f"AWSTools initialized successfully for region '{region_name}'.")
        except NoCredentialsError:
            raise ConnectionError("AWS credentials not found. Please configure them (e.g., via `aws configure`).")
        except ClientError as e:
            raise ConnectionError(f"AWS client error on initialization: {e}")

    def ec2_describe_instances(self) -> Dict[str, Any]:
        """Describes all EC2 instances in the configured region."""
        try:
            return self.ec2.describe_instances()
        except ClientError as e:
            logger.error(f"Failed to describe EC2 instances: {e}")
            return {"Error": str(e)}

    def s3_list_buckets(self) -> Dict[str, Any]:
        """Lists all S3 buckets."""
        try:
            return self.s3.list_buckets()
        except ClientError as e:
            logger.error(f"Failed to list S3 buckets: {e}")
            return {"Error": str(e)}


class GCPTools:
    """A functional toolbox for interacting with Google Cloud Platform."""
    def __init__(self, project_id: Optional[str] = None):
        if not GCP_SDK_AVAILABLE:
            raise ImportError("GCP SDKs are required. 'pip install google-cloud-compute google-cloud-storage'")
        try:
            self.compute_client = compute_v1.InstancesClient()
            self.storage_client = storage.Client(project=project_id)
            self.project_id = project_id or self.storage_client.project
            logger.info(f"GCPTools initialized successfully for project '{self.project_id}'.")
        except Exception as e:
            raise ConnectionError(f"GCP initialization failed. Have you authenticated (e.g., `gcloud auth application-default login`)? Error: {e}")

    def compute_instances_list(self, zone: str) -> Dict[str, Any]:
        """Lists all VM instances in a given zone."""
        try:
            instances = self.compute_client.list(project=self.project_id, zone=zone)
            # The response is an iterator of complex objects; we convert it to a dict for consistency
            return {"items": [type(instance).to_dict(instance) for instance in instances]}
        except gcp_exceptions.PermissionDenied as e:
            logger.error(f"GCP Permission Denied for listing instances in zone {zone}: {e}")
            return {"Error": str(e)}
        except Exception as e:
            logger.error(f"Failed to list GCP instances: {e}")
            return {"Error": str(e)}


class AzureTools:
    """A functional toolbox for interacting with Microsoft Azure."""
    def __init__(self, subscription_id: Optional[str] = None):
        if not AZURE_SDK_AVAILABLE:
            raise ImportError("Azure SDKs are required. 'pip install azure-identity azure-mgmt-compute'")
        try:
            self.credential = DefaultAzureCredential()
            # The SDK will find the subscription ID from the environment if not provided.
            self.subscription_id = subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
            if not self.subscription_id:
                raise ValueError("Azure Subscription ID not found. Provide it or set AZURE_SUBSCRIPTION_ID env var.")
            self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            logger.info(f"AzureTools initialized successfully for subscription '{self.subscription_id[:8]}...'.")
        except (ClientAuthenticationError, ValueError) as e:
            raise ConnectionError(f"Azure authentication failed. Have you authenticated (e.g., `az login`)? Error: {e}")

    def vm_list_all(self) -> List[Dict[str, Any]]:
        """Lists all Virtual Machines in the subscription."""
        try:
            vms = self.compute_client.virtual_machines.list_all()
            # Convert SDK objects to dictionaries
            return [vm.as_dict() for vm in vms]
        except ClientAuthenticationError as e:
            logger.error(f"Azure authentication error while listing VMs: {e}")
            return [{"Error": str(e)}]
        except Exception as e:
            logger.error(f"Failed to list Azure VMs: {e}")
            return [{"Error": str(e)}]


# --- Example Usage ---
if __name__ == "__main__":
    import json
    
    def pretty_print(data: Any):
        print(json.dumps(data, indent=2, default=str))

    print("=========================================================")
    print("=== Integrated Cloud Tools Prototype (Live API Calls) ===")
    print("=========================================================")
    print("!!! PREREQUISITE: For each cloud provider you want to test, you must be authenticated in your shell. !!!")
    
    # --- 1. AWS Tools Demonstration ---
    print("\n\n---------- [ AWS Demo ] ----------")
    if AWS_SDK_AVAILABLE:
        try:
            aws_tools = AWSTools(region_name="us-east-1")
            print("\n[AWS] Describing EC2 Instances...")
            ec2_instances = aws_tools.ec2_describe_instances()
            print("Response (first reservation shown):")
            pretty_print(ec2_instances.get("Reservations", [{}])[0])
            
            print("\n[AWS] Listing S3 Buckets...")
            s3_buckets = aws_tools.s3_list_buckets()
            print("Response:")
            pretty_print(s3_buckets)
        except (ImportError, ConnectionError) as e:
            print(f"Skipping AWS Demo: {e}")
    else:
        print("Skipping AWS Demo: boto3 SDK not installed.")
        
    # --- 2. GCP Tools Demonstration ---
    print("\n\n---------- [ GCP Demo ] ----------")
    if GCP_SDK_AVAILABLE:
        try:
            gcp_tools = GCPTools()
            print("\n[GCP] Listing Compute Engine Instances in 'us-central1-a'...")
            gce_instances = gcp_tools.compute_instances_list(zone="us-central1-a")
            print("Response (first instance shown):")
            pretty_print(gce_instances.get("items", [{}])[0])
        except (ImportError, ConnectionError) as e:
            print(f"Skipping GCP Demo: {e}")
    else:
        print("Skipping GCP Demo: google-cloud SDKs not installed.")
        
    # --- 3. Azure Tools Demonstration ---
    print("\n\n---------- [ Azure Demo ] ----------")
    if AZURE_SDK_AVAILABLE:
        try:
            azure_tools = AzureTools()
            print("\n[Azure] Listing all Virtual Machines in subscription...")
            azure_vms = azure_tools.vm_list_all()
            print("Response (first VM shown):")
            pretty_print(azure_vms[0] if azure_vms else {})
        except (ImportError, ConnectionError, ValueError) as e:
            print(f"Skipping Azure Demo: {e}")
    else:
        print("Skipping Azure Demo: azure SDKs not installed.")

    print("\n=========================================================")
    print("=== Cloud Tools Prototype Complete ===")
    print("=========================================================")
