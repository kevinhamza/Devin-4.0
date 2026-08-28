# modules/cloud_tools.py
"""
Cloud Tools Module
===================
This module provides utilities for managing cloud resources, including 
provisioning, monitoring, and scaling. It integrates with multiple cloud providers 
to offer a unified interface for resource management.
"""

import boto3
from google.cloud import storage
from azure.mgmt.compute import ComputeManagementClient
from azure.identity import DefaultAzureCredential
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class manage_cloud_resources:
    def __init__(self):
        self.aws_clients = {}
        self.gcp_clients = {}
        self.azure_clients = {}

    # AWS Resource Management
    def aws_connect(self, service_name, region_name='us-east-1'):
        """
        Connects to an AWS service.
        """
        try:
            self.aws_clients[service_name] = boto3.client(service_name, region_name=region_name)
            logging.info(f"Connected to AWS {service_name} service in {region_name} region.")
        except Exception as e:
            logging.error(f"Failed to connect to AWS {service_name}: {e}")

    def aws_create_ec2_instance(self, ami_id, instance_type, key_name, security_group):
        """
        Creates an EC2 instance on AWS.
        """
        try:
            ec2_client = self.aws_clients.get('ec2')
            if not ec2_client:
                self.aws_connect('ec2')
                ec2_client = self.aws_clients.get('ec2')

            response = ec2_client.run_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                KeyName=key_name,
                SecurityGroupIds=[security_group],
                MinCount=1,
                MaxCount=1
            )
            instance_id = response['Instances'][0]['InstanceId']
            logging.info(f"Created AWS EC2 instance with ID: {instance_id}")
            return instance_id
        except Exception as e:
            logging.error(f"Failed to create EC2 instance: {e}")

    # GCP Resource Management
    def gcp_connect(self, project_id):
        """
        Connects to GCP storage.
        """
        try:
            client = storage.Client(project=project_id)
            self.gcp_clients['storage'] = client
            logging.info("Connected to GCP Storage.")
        except Exception as e:
            logging.error(f"Failed to connect to GCP: {e}")

    def gcp_create_bucket(self, bucket_name):
        """
        Creates a storage bucket in GCP.
        """
        try:
            storage_client = self.gcp_clients.get('storage')
            if not storage_client:
                raise ValueError("GCP Storage client is not initialized.")

            bucket = storage_client.create_bucket(bucket_name)
            logging.info(f"Created GCP bucket: {bucket.name}")
            return bucket.name
        except Exception as e:
            logging.error(f"Failed to create GCP bucket: {e}")

    # Azure Resource Management
    def azure_connect(self, subscription_id):
        """
        Connects to Azure compute services.
        """
        try:
            credential = DefaultAzureCredential()
            compute_client = ComputeManagementClient(credential, subscription_id)
            self.azure_clients['compute'] = compute_client
            logging.info("Connected to Azure Compute Management.")
        except Exception as e:
            logging.error(f"Failed to connect to Azure: {e}")

    def azure_create_vm(self, resource_group, vm_name, location, image_reference, size):
        """
        Creates a Virtual Machine in Azure.
        """
        try:
            compute_client = self.azure_clients.get('compute')
            if not compute_client:
                raise ValueError("Azure Compute client is not initialized.")

            vm_parameters = {
                'location': location,
                'storage_profile': {'image_reference': image_reference},
                'hardware_profile': {'vm_size': size},
                'os_profile': {
                    'computer_name': vm_name,
                    'admin_username': 'azureuser',
                    'admin_password': 'Azure123456!'  # Secure password management needed
                },
                'network_profile': {
                    'network_interfaces': [{'id': '/subscriptions/.../networkInterfaces/myNIC'}]
                }
            }
            async_vm_creation = compute_client.virtual_machines.begin_create_or_update(
                resource_group, vm_name, vm_parameters
            )
            result = async_vm_creation.result()
            logging.info(f"Created Azure VM: {vm_name} in resource group: {resource_group}")
            return result
        except Exception as e:
            logging.error(f"Failed to create Azure VM: {e}")

# Example usage
if __name__ == "__main__":
    cloud_tools = CloudTools()

    # AWS Example
    cloud_tools.aws_connect('ec2')
    cloud_tools.aws_create_ec2_instance(
        ami_id='ami-0abcdef1234567890',
        instance_type='t2.micro',
        key_name='my-key-pair',
        security_group='sg-0123456789abcdef0'
    )

    # GCP Example
    cloud_tools.gcp_connect('my-gcp-project-id')
    cloud_tools.gcp_create_bucket('my-new-gcp-bucket')

    # Azure Example
    cloud_tools.azure_connect('my-azure-subscription-id')
    cloud_tools.azure_create_vm(
        resource_group='myResourceGroup',
        vm_name='myVM',
        location='eastus',
        image_reference={
            'publisher': 'Canonical',
            'offer': 'UbuntuServer',
            'sku': '18.04-LTS',
            'version': 'latest'
        },
        size='Standard_B1s'
    )
