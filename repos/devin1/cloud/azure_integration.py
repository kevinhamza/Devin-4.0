"""
cloud/azure_integration.py

This module handles integration with Microsoft Azure cloud services, providing support for
key functionalities such as virtual machines, storage accounts, AI services, and networking.
"""

import os
import azure.identity
import azure.mgmt.compute
import azure.mgmt.storage
import azure.mgmt.network
import azure.ai.textanalytics
import azure.core.credentials
import logging

# Constants
AZURE_CREDENTIALS_ENV_VARS = ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"]
DEFAULT_REGION = "East US"

# Set up logging for better debugging and tracking
logging.basicConfig(level=logging.INFO)


class AzureIntegration:
    def __init__(self, subscription_id, region=DEFAULT_REGION):
        self.subscription_id = subscription_id
        self.region = region
        self.credentials = self.get_azure_credentials()

    # Azure Authentication
    @staticmethod
    def get_azure_credentials():
        """
        Retrieves Azure credentials from environment variables.
        """
        try:
            for var in AZURE_CREDENTIALS_ENV_VARS:
                if var not in os.environ:
                    raise EnvironmentError(f"{var} is not set in the environment variables.")
            credentials = azure.identity.ClientSecretCredential(
                tenant_id=os.environ["AZURE_TENANT_ID"],
                client_id=os.environ["AZURE_CLIENT_ID"],
                client_secret=os.environ["AZURE_CLIENT_SECRET"]
            )
            return credentials
        except Exception as e:
            logging.error(f"Error retrieving Azure credentials: {e}")
            raise RuntimeError(f"Error retrieving Azure credentials: {e}")

    # Azure Virtual Machine Operations
    def list_virtual_machines(self):
        """
        Lists all virtual machines in a given subscription.
        """
        try:
            compute_client = azure.mgmt.compute.ComputeManagementClient(self.credentials, self.subscription_id)
            vms = compute_client.virtual_machines.list_all()
            return [vm.name for vm in vms]
        except Exception as e:
            logging.error(f"Error listing virtual machines: {e}")
            raise RuntimeError(f"Error listing virtual machines: {e}")

    def create_virtual_machine(self, resource_group, vm_name, vm_params):
        """
        Creates a virtual machine in Azure.
        """
        try:
            compute_client = azure.mgmt.compute.ComputeManagementClient(self.credentials, self.subscription_id)
            compute_client.virtual_machines.begin_create_or_update(resource_group, vm_name, vm_params)
            logging.info(f"Virtual machine '{vm_name}' created successfully.")
            return f"Virtual machine '{vm_name}' created successfully."
        except Exception as e:
            logging.error(f"Error creating virtual machine: {e}")
            raise RuntimeError(f"Error creating virtual machine: {e}")

    # Azure Storage Account Operations
    def create_storage_account(self, resource_group, account_name):
        """
        Creates a storage account in Azure.
        """
        try:
            storage_client = azure.mgmt.storage.StorageManagementClient(self.credentials, self.subscription_id)
            storage_params = {
                "location": self.region,
                "sku": {"name": "Standard_LRS"},
                "kind": "StorageV2",
            }
            storage_client.storage_accounts.begin_create(resource_group, account_name, storage_params)
            logging.info(f"Storage account '{account_name}' created successfully.")
            return f"Storage account '{account_name}' created successfully."
        except Exception as e:
            logging.error(f"Error creating storage account: {e}")
            raise RuntimeError(f"Error creating storage account: {e}")

    # Azure Networking Operations
    def list_virtual_networks(self):
        """
        Lists all virtual networks in a given subscription.
        """
        try:
            network_client = azure.mgmt.network.NetworkManagementClient(self.credentials, self.subscription_id)
            vnets = network_client.virtual_networks.list_all()
            return [vnet.name for vnet in vnets]
        except Exception as e:
            logging.error(f"Error listing virtual networks: {e}")
            raise RuntimeError(f"Error listing virtual networks: {e}")

    # Azure AI Services (Text Analytics Example)
    def analyze_text(self, endpoint, api_key, text):
        """
        Analyzes text using Azure's Text Analytics service.
        """
        try:
            text_analytics_client = azure.ai.textanalytics.TextAnalyticsClient(
                endpoint=endpoint,
                credential=azure.core.credentials.AzureKeyCredential(api_key)
            )
            result = text_analytics_client.analyze_sentiment([text])[0]
            return {
                "sentiment": result.sentiment,
                "confidence_scores": result.confidence_scores
            }
        except Exception as e:
            logging.error(f"Error analyzing text: {e}")
            raise RuntimeError(f"Error analyzing text: {e}")


# Main Entry Point for Testing
if __name__ == "__main__":
    try:
        # Set subscription and resource details
        SUBSCRIPTION_ID = "your_subscription_id"
        RESOURCE_GROUP = "your_resource_group"
        VM_NAME = "test-vm"
        STORAGE_ACCOUNT_NAME = "teststorageaccount"
        TEXT = "Azure is a powerful cloud platform."
        
        # Initialize AzureIntegration
        azure_integration = AzureIntegration(SUBSCRIPTION_ID)

        # Perform operations
        logging.info("Listing Virtual Machines:")
        print(azure_integration.list_virtual_machines())

        logging.info("\nCreating Virtual Machine:")
        vm_params = {
            # Add VM creation parameters here
        }
        print(azure_integration.create_virtual_machine(RESOURCE_GROUP, VM_NAME, vm_params))

        logging.info("\nCreating Storage Account:")
        print(azure_integration.create_storage_account(RESOURCE_GROUP, STORAGE_ACCOUNT_NAME))

        logging.info("\nListing Virtual Networks:")
        print(azure_integration.list_virtual_networks())

        logging.info("\nAnalyzing Text Sentiment:")
        print(azure_integration.analyze_text("your_text_analytics_endpoint", "your_text_analytics_api_key", TEXT))

    except Exception as e:
        logging.error(f"Error: {e}")
