# # Devin/modules/cloud_integration_utilities.py
# # Purpose: Provides shared, stateless utility functions and data models
# #          for all cloud integration modules to use.
# # Provides cloud integration utilities 🛠️

# import logging
# import json
# import os
# from enum import Enum
# from dataclasses import dataclass, field
# from typing import List, Dict, Any, Optional

# # Configure basic logging
# logger = logging.getLogger("CloudIntegrationUtilities")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class CloudProvider(Enum):
#     """Standardized enumeration for cloud providers."""
#     AWS = "aws"
#     GCP = "gcp"
#     AZURE = "azure"

# class CloudResourceType(Enum):
#     """Standardized enumeration for cloud resource types."""
#     VIRTUAL_MACHINE = "vm"
#     STORAGE_BUCKET = "storage_bucket"
#     DATABASE = "database"
#     SECURITY_GROUP = "security_group"

# @dataclass
# class NormalizedCloudResource:
#     """A standardized dataclass to represent any cloud resource."""
#     uid: str # A unique ID for this resource within our system
#     provider_id: str # The resource ID from the cloud provider (e.g., 'i-12345...')
#     name: str
#     provider: CloudProvider
#     resource_type: CloudResourceType
#     region: Optional[str] = None
#     status: Optional[str] = None
#     tags: Dict[str, str] = field(default_factory=dict)
#     public_ip: Optional[str] = None
#     private_ip: Optional[str] = None
#     created_at: Optional[str] = None
#     metadata: Dict[str, Any] = field(default_factory=dict) # For any other provider-specific info


# class DataNormalizer:
#     """
#     A stateless utility class with methods to convert provider-specific
#     API responses into the standardized 'NormalizedCloudResource' format.
#     """

#     @staticmethod
#     def from_aws_ec2_instance(instance_data: Dict[str, Any], region: str) -> NormalizedCloudResource:
#         """Normalizes a dictionary from an AWS EC2 describe_instances call."""
#         logger.debug(f"Normalizing AWS EC2 instance data: {instance_data.get('InstanceId')}")
#         tags = {tag['Key']: tag['Value'] for tag in instance_data.get('Tags', [])}
        
#         return NormalizedCloudResource(
#             uid=f"aws_vm_{instance_data.get('InstanceId')}",
#             provider_id=instance_data.get('InstanceId'),
#             name=tags.get('Name', instance_data.get('InstanceId', 'unnamed')),
#             provider=CloudProvider.AWS,
#             resource_type=CloudResourceType.VIRTUAL_MACHINE,
#             region=region,
#             status=instance_data.get('State', {}).get('Name'),
#             tags=tags,
#             public_ip=instance_data.get('PublicIpAddress'),
#             private_ip=instance_data.get('PrivateIpAddress'),
#             created_at=instance_data.get('LaunchTime'),
#             metadata={
#                 "instance_type": instance_data.get('InstanceType'),
#                 "image_id": instance_data.get('ImageId'),
#                 "vpc_id": instance_data.get('VpcId')
#             }
#         )

#     @staticmethod
#     def from_gcp_compute_instance(instance_data: Dict[str, Any], zone: str) -> NormalizedCloudResource:
#         """Normalizes a dictionary from a GCP Compute Engine instances().list call."""
#         logger.debug(f"Normalizing GCP Compute instance data: {instance_data.get('name')}")
        
#         # GCP network info is more complex
#         private_ip = instance_data.get('networkInterfaces', [{}])[0].get('networkIP')
#         public_ip = instance_data.get('networkInterfaces', [{}])[0].get('accessConfigs', [{}])[0].get('natIP')

#         return NormalizedCloudResource(
#             uid=f"gcp_vm_{instance_data.get('id')}",
#             provider_id=instance_data.get('id'),
#             name=instance_data.get('name', 'unnamed'),
#             provider=CloudProvider.GCP,
#             resource_type=CloudResourceType.VIRTUAL_MACHINE,
#             region=zone.rsplit('-', 1)[0], # Convert zone 'us-central1-a' to region 'us-central1'
#             status=instance_data.get('status'),
#             tags=instance_data.get('labels', {}),
#             public_ip=public_ip,
#             private_ip=private_ip,
#             created_at=instance_data.get('creationTimestamp'),
#             metadata={
#                 "machine_type": instance_data.get('machineType', '').split('/')[-1],
#                 "zone": zone
#             }
#         )
        
#     # Add similar normalizers for Azure VMs, S3 buckets, GCS buckets, etc.
#     @staticmethod
#     def from_aws_s3_bucket(bucket_data: Dict[str, Any]) -> NormalizedCloudResource:
#         """Normalizes a dictionary from an AWS S3 list_buckets call."""
#         logger.debug(f"Normalizing AWS S3 bucket data: {bucket_data.get('Name')}")
#         name = bucket_data.get('Name')
#         return NormalizedCloudResource(
#             uid=f"aws_storage_bucket_{name}",
#             provider_id=name,
#             name=name,
#             provider=CloudProvider.AWS,
#             resource_type=CloudResourceType.STORAGE_BUCKET,
#             status="available", # S3 buckets don't have a simple status like VMs
#             created_at=bucket_data.get('CreationDate'),
#         )

# class TagManager:
#     """A utility to enforce consistent tagging policies."""
    
#     REQUIRED_TAGS = ["project", "owner", "cost-center"]
    
#     @staticmethod
#     def validate_tags(tags: Dict[str, str]) -> Dict[str, List[str]]:
#         """
#         Validates a set of tags against a required policy.
#         Returns a dictionary of missing and empty tags.
#         """
#         missing = [key for key in TagManager.REQUIRED_TAGS if key not in tags]
#         empty = [key for key, value in tags.items() if key in TagManager.REQUIRED_TAGS and not value]
        
#         if missing or empty:
#             logger.warning(f"Tag validation found issues. Missing: {missing}, Empty: {empty}")
#         else:
#             logger.info("Tag validation passed.")
        
#         return {"missing_tags": missing, "empty_tags": empty}

# class CostEstimator:
#     """A conceptual utility to provide rough cost estimates."""
    
#     # Highly simplified, conceptual price list ($/hour)
#     CONCEPTUAL_PRICES = {
#         "aws": {"t2.micro": 0.012, "m5.large": 0.096},
#         "gcp": {"e2-medium": 0.021, "n1-standard-1": 0.047},
#         "azure": {"Standard_B1s": 0.01, "Standard_DS2_v2": 0.15}
#     }

#     @staticmethod
#     def estimate_monthly_vm_cost(provider: CloudProvider, instance_type: str) -> Optional[float]:
#         """Estimates the monthly cost of a given VM instance type."""
#         hourly_rate = CostEstimator.CONCEPTUAL_PRICES.get(provider.value, {}).get(instance_type)
#         if hourly_rate is None:
#             logger.warning(f"No price data for instance type '{instance_type}' on provider '{provider.value}'.")
#             return None
        
#         monthly_cost = hourly_rate * 24 * 30 # Simple estimation
#         logger.info(f"Estimated monthly cost for '{instance_type}' on '{provider.value}': ${monthly_cost:.2f}")
#         return monthly_cost

# class CredentialLoader:
#     """A conceptual utility for securely loading credentials."""

#     @staticmethod
#     def load_credentials_conceptual(provider: CloudProvider) -> Dict[str, str]:
#         """
#         Conceptually loads credentials from environment variables.
#         In a real system, this would integrate with a secure vault (e.g., HashiCorp Vault, AWS Secrets Manager).
#         """
#         logger.info(f"CONCEPTUAL: Loading credentials for '{provider.value}' from secure source (e.g., env vars, vault).")
#         if provider == CloudProvider.AWS:
#             return {
#                 "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", "DUMMY_AWS_KEY_ID"),
#                 "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", "DUMMY_AWS_SECRET")
#             }
#         elif provider == CloudProvider.GCP:
#             return {"gcp_credentials_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/to/gcp.json")}
#         # ... and so on for other providers
#         return {}

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Cloud Integration Utilities Prototype 🛠️ ===")
#     print("=========================================================")
    
#     # --- 1. Data Normalization Demonstration ---
#     print("\n--- Utility 1: Data Normalization ---")
    
#     # A sample raw dictionary response from a conceptual AWS EC2 API call
#     aws_ec2_raw_data = {
#         'InstanceId': 'i-01a2b3c4d5e6f7g8h',
#         'ImageId': 'ami-0c55b159cbfafe1f0',
#         'InstanceType': 't2.micro',
#         'State': {'Name': 'running'},
#         'PrivateIpAddress': '172.31.10.20',
#         'PublicIpAddress': '54.123.45.67',
#         'LaunchTime': '2025-06-07T10:00:00Z',
#         'Tags': [{'Key': 'Name', 'Value': 'WebServer-Prod'}, {'Key': 'project', 'Value': 'Devin'}]
#     }
    
#     print("\nOriginal AWS EC2 Data (dict):")
#     print(json.dumps(aws_ec2_raw_data, indent=2))
    
#     # Use the normalizer to convert it
#     normalized_resource = DataNormalizer.from_aws_ec2_instance(aws_ec2_raw_data, region="us-east-1")
    
#     print("\nNormalized Resource (dataclass):")
#     print(json.dumps(normalized_resource.__dict__, indent=2, default=str))


#     # --- 2. Tag Management Demonstration ---
#     print("\n\n--- Utility 2: Tag Management ---")
#     print("Validating tags for the normalized resource...")
#     # The 'cost-center' tag is missing, and 'owner' will be added as empty
#     incomplete_tags = normalized_resource.tags
#     incomplete_tags['owner'] = ''
#     validation_result = TagManager.validate_tags(incomplete_tags)
#     print(f"Validation Result: {validation_result}")
    
#     print("\nValidating a compliant set of tags...")
#     compliant_tags = {'project': 'Devin', 'owner': 'ai_team', 'cost-center': 'R&D'}
#     validation_result_good = TagManager.validate_tags(compliant_tags)
#     print(f"Validation Result: {validation_result_good}")


#     # --- 3. Cost Estimation Demonstration ---
#     print("\n\n--- Utility 3: Cost Estimation ---")
#     instance_type_to_estimate = normalized_resource.metadata['instance_type']
#     estimated_cost = CostEstimator.estimate_monthly_vm_cost(
#         provider=normalized_resource.provider,
#         instance_type=instance_type_to_estimate
#     )
#     if estimated_cost is not None:
#         print(f"The conceptual monthly cost for a '{instance_type_to_estimate}' on {normalized_resource.provider.value} is approx. ${estimated_cost:.2f}")

#     # --- 4. Credential Loading Demonstration ---
#     print("\n\n--- Utility 4: Credential Loading ---")
#     aws_creds = CredentialLoader.load_credentials_conceptual(CloudProvider.AWS)
#     print(f"Conceptually loaded AWS credentials: {aws_creds}")

#     print("\n=========================================================")
#     print("=== Cloud Utilities Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/cloud_integration_utilities.py
# Purpose: Provides shared, stateless utility functions and data models
#          for normalizing and managing multi-cloud resources.

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

# Configure basic logging
logger = logging.getLogger("CloudIntegrationUtilities")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class CloudProvider(Enum):
    """Standardized enumeration for cloud providers."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"

class CloudResourceType(Enum):
    """Standardized enumeration for cloud resource types."""
    VIRTUAL_MACHINE = "vm"
    STORAGE_BUCKET = "storage_bucket"
    DATABASE = "database"

@dataclass
class NormalizedCloudResource:
    """A standardized dataclass to represent any cloud resource."""
    uid: str
    provider_id: str
    name: str
    provider: CloudProvider
    resource_type: CloudResourceType
    region: Optional[str] = None
    status: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    public_ip: Optional[str] = None
    private_ip: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataNormalizer:
    """
    A stateless utility class to convert provider-specific API responses
    into the standardized 'NormalizedCloudResource' format.
    """

    # --- VIRTUAL MACHINE NORMALIZERS ---
    @staticmethod
    def from_aws_ec2_instance(d: Dict, region: str) -> NormalizedCloudResource:
        tags = {tag['Key']: tag['Value'] for tag in d.get('Tags', [])}
        return NormalizedCloudResource(
            uid=f"aws_vm_{d.get('InstanceId')}", provider_id=d.get('InstanceId'),
            name=tags.get('Name', d.get('InstanceId', 'unnamed')),
            provider=CloudProvider.AWS, resource_type=CloudResourceType.VIRTUAL_MACHINE,
            region=region, status=d.get('State', {}).get('Name'), tags=tags,
            public_ip=d.get('PublicIpAddress'), private_ip=d.get('PrivateIpAddress'),
            created_at=str(d.get('LaunchTime')),
            metadata={"instance_type": d.get('InstanceType'), "image_id": d.get('ImageId')}
        )

    @staticmethod
    def from_gcp_compute_instance(d: Dict, zone: str) -> NormalizedCloudResource:
        private_ip = d.get('networkInterfaces', [{}])[0].get('networkIP')
        public_ip = d.get('networkInterfaces', [{}])[0].get('accessConfigs', [{}])[0].get('natIP')
        region = zone.rsplit('-', 1)[0] if zone else None
        return NormalizedCloudResource(
            uid=f"gcp_vm_{d.get('id')}", provider_id=d.get('id'),
            name=d.get('name', 'unnamed'), provider=CloudProvider.GCP,
            resource_type=CloudResourceType.VIRTUAL_MACHINE, region=region,
            status=d.get('status'), tags=d.get('labels', {}), public_ip=public_ip,
            private_ip=private_ip, created_at=d.get('creationTimestamp'),
            metadata={"machine_type": d.get('machineType', '').split('/')[-1], "zone": zone}
        )

    @staticmethod
    def from_azure_vm(d: Dict) -> NormalizedCloudResource:
        # Azure VM data is nested differently. This is a simplified normalization.
        props = d.get('properties', {})
        os_profile = props.get('osProfile', {})
        hardware_profile = props.get('hardwareProfile', {})
        return NormalizedCloudResource(
            uid=f"azure_vm_{d.get('id')}", provider_id=d.get('id'),
            name=d.get('name', 'unnamed'), provider=CloudProvider.AZURE,
            resource_type=CloudResourceType.VIRTUAL_MACHINE, region=d.get('location'),
            status=props.get('provisioningState'), tags=d.get('tags', {}),
            # Public/private IPs require another API call in Azure, so we'll omit them here for simplicity
            created_at=str(props.get('timeCreated')),
            metadata={"vm_size": hardware_profile.get('vmSize'), "computer_name": os_profile.get('computerName')}
        )

    # --- STORAGE BUCKET NORMALIZERS ---
    @staticmethod
    def from_aws_s3_bucket(d: Dict) -> NormalizedCloudResource:
        name = d.get('Name')
        return NormalizedCloudResource(
            uid=f"aws_bucket_{name}", provider_id=name, name=name,
            provider=CloudProvider.AWS, resource_type=CloudResourceType.STORAGE_BUCKET,
            created_at=str(d.get('CreationDate'))
        )
        
    @staticmethod
    def from_gcp_storage_bucket(d: Dict) -> NormalizedCloudResource:
        name = d.get('name')
        return NormalizedCloudResource(
            uid=f"gcp_bucket_{name}", provider_id=d.get('id'), name=name,
            provider=CloudProvider.GCP, resource_type=CloudResourceType.STORAGE_BUCKET,
            region=d.get('location'), created_at=d.get('timeCreated')
        )


class TagManager:
    """A utility to enforce consistent tagging policies."""
    REQUIRED_TAGS = ["project", "owner", "cost-center"]
    
    @staticmethod
    def validate_tags(tags: Dict[str, str]) -> Dict[str, List[str]]:
        missing = [key for key in TagManager.REQUIRED_TAGS if key not in tags]
        empty = [key for key, value in tags.items() if key in TagManager.REQUIRED_TAGS and not value]
        if missing or empty:
            logger.warning(f"Tag validation found issues. Missing: {missing}, Empty: {empty}")
        return {"missing_tags": missing, "empty_tags": empty}


class CostEstimator:
    """A utility to provide rough cost estimates based on a conceptual price list."""
    CONCEPTUAL_PRICES = {
        "aws": {"t2.micro": 0.012, "m5.large": 0.096, "c5.xlarge": 0.17},
        "gcp": {"e2-medium": 0.021, "n2-standard-2": 0.095, "c2-standard-4": 0.21},
        "azure": {"Standard_B1s": 0.01, "Standard_D2s_v3": 0.096, "Standard_F4s_v2": 0.20}
    }

    @staticmethod
    def estimate_monthly_vm_cost(provider: CloudProvider, instance_type: str) -> Optional[float]:
        hourly_rate = CostEstimator.CONCEPTUAL_PRICES.get(provider.value, {}).get(instance_type)
        if hourly_rate is None: return None
        return hourly_rate * 24 * 30


# --- Example Usage ---
if __name__ == "__main__":
    import json

    print("=========================================================")
    print("=== Integrated Cloud Integration Utilities 🛠️ ===")
    print("=========================================================")
    
    # --- 1. Data Normalization Demonstration ---
    print("\n--- Utility 1: Data Normalization ---")
    
    # Sample raw AWS EC2 API response data
    aws_ec2_raw_data = {'InstanceId': 'i-01a2b3c4d5e6f7g8h', 'InstanceType': 't2.micro', 'State': {'Name': 'running'}, 'PublicIpAddress': '54.123.45.67', 'PrivateIpAddress': '172.31.10.20', 'LaunchTime': '2025-08-10T10:00:00Z', 'Tags': [{'Key': 'Name', 'Value': 'WebServer-Prod'}]}
    
    # Sample raw GCP Compute Engine API response data
    gcp_vm_raw_data = {'id': '1234567890123456789', 'name': 'gce-dev-instance', 'machineType': 'zones/us-central1-a/machineTypes/e2-medium', 'status': 'RUNNING', 'networkInterfaces': [{'networkIP': '10.128.0.2', 'accessConfigs': [{'natIP': '34.67.89.10'}]}], 'creationTimestamp': '2025-08-09T12:00:00.000-07:00', 'labels': {'project': 'devin-ops'}}

    print("\nOriginal AWS EC2 Data:")
    print(json.dumps(aws_ec2_raw_data, indent=2))
    normalized_aws = DataNormalizer.from_aws_ec2_instance(aws_ec2_raw_data, region="us-east-1")
    print("\n---> Normalized AWS Resource:")
    print(json.dumps(normalized_aws.__dict__, indent=2, default=str))

    print("\n\nOriginal GCP VM Data:")
    print(json.dumps(gcp_vm_raw_data, indent=2))
    normalized_gcp = DataNormalizer.from_gcp_compute_instance(gcp_vm_raw_data, zone="us-central1-a")
    print("\n---> Normalized GCP Resource:")
    print(json.dumps(normalized_gcp.__dict__, indent=2, default=str))

    # --- 2. Tag Management Demonstration ---
    print("\n\n--- Utility 2: Tag Management ---")
    print("Validating tags for the (non-compliant) GCP resource...")
    validation_result = TagManager.validate_tags(normalized_gcp.tags)
    print(f"Validation Result: {validation_result}")
    
    # --- 3. Cost Estimation Demonstration ---
    print("\n\n--- Utility 3: Cost Estimation ---")
    cost = CostEstimator.estimate_monthly_vm_cost(normalized_aws.provider, normalized_aws.metadata['instance_type'])
    print(f"Estimated monthly cost for '{normalized_aws.name}' ({normalized_aws.metadata['instance_type']}): ${cost:.2f}")

    print("\n=========================================================")
    print("=== Cloud Utilities Prototype Complete ===")
    print("=========================================================")
