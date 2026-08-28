"""
Cloud Integration Module
=========================
Manages AWS, GCP, Azure, and private cloud environments, providing tools for cloud instance control, storage management, and service integration.
"""

import boto3
from google.cloud import storage as gcp_storage
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
import paramiko


class CloudIntegrationModule:
    """
    CloudIntegrationModule provides functionalities to interact with AWS, GCP, Azure, and private cloud platforms.
    """

    def __init__(self):
        print("[INFO] Cloud Integration Module initialized.")

    # ----------------------- AWS INTEGRATION ----------------------- #

    def aws_list_instances(self, aws_access_key, aws_secret_key, region):
        """
        Lists all EC2 instances in the specified AWS region.

        Args:
            aws_access_key (str): AWS access key.
            aws_secret_key (str): AWS secret key.
            region (str): AWS region.

        Returns:
            list: List of EC2 instances.
        """
        print(f"[INFO] Connecting to AWS region: {region}")
        ec2_client = boto3.client(
            'ec2',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        instances = ec2_client.describe_instances()
        return instances.get('Reservations', [])

    def aws_start_instance(self, aws_access_key, aws_secret_key, region, instance_id):
        """
        Starts an EC2 instance.

        Args:
            aws_access_key (str): AWS access key.
            aws_secret_key (str): AWS secret key.
            region (str): AWS region.
            instance_id (str): EC2 instance ID.

        Returns:
            str: Status of the operation.
        """
        print(f"[INFO] Starting AWS EC2 instance: {instance_id}")
        ec2_client = boto3.client(
            'ec2',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        response = ec2_client.start_instances(InstanceIds=[instance_id])
        return response['StartingInstances'][0]['CurrentState']['Name']

    # ----------------------- GCP INTEGRATION ----------------------- #

    def gcp_upload_file(self, bucket_name, source_file_path, destination_blob_name):
        """
        Uploads a file to a GCP Cloud Storage bucket.

        Args:
            bucket_name (str): Name of the GCP storage bucket.
            source_file_path (str): Path to the file on the local system.
            destination_blob_name (str): Destination name in the bucket.

        Returns:
            bool: True if successful, False otherwise.
        """
        print(f"[INFO] Uploading file to GCP bucket: {bucket_name}")
        client = gcp_storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        print(f"[INFO] File uploaded to {destination_blob_name} in bucket {bucket_name}.")
        return True

    # ----------------------- AZURE INTEGRATION ----------------------- #

    def azure_list_vms(self, subscription_id):
        """
        Lists all virtual machines in an Azure subscription.

        Args:
            subscription_id (str): Azure subscription ID.

        Returns:
            list: List of Azure VMs.
        """
        print("[INFO] Connecting to Azure...")
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, subscription_id)
        vms = compute_client.virtual_machines.list_all()
        return [vm.name for vm in vms]

    def azure_start_vm(self, subscription_id, resource_group_name, vm_name):
        """
        Starts an Azure virtual machine.

        Args:
            subscription_id (str): Azure subscription ID.
            resource_group_name (str): Resource group name.
            vm_name (str): Name of the virtual machine.

        Returns:
            bool: True if successful, False otherwise.
        """
        print(f"[INFO] Starting Azure VM: {vm_name}")
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, subscription_id)
        async_vm_start = compute_client.virtual_machines.begin_start(resource_group_name, vm_name)
        async_vm_start.result()  # Wait for the operation to complete.
        print(f"[INFO] Azure VM {vm_name} started successfully.")
        return True

    # ----------------------- PRIVATE CLOUD INTEGRATION ----------------------- #

    def private_cloud_execute_command(self, host, username, password, command):
        """
        Executes a shell command on a private cloud server via SSH.

        Args:
            host (str): Server IP or hostname.
            username (str): SSH username.
            password (str): SSH password.
            command (str): Command to execute.

        Returns:
            str: Output of the command.
        """
        print(f"[INFO] Executing command on private cloud server: {host}")
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=host, username=username, password=password)
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode('utf-8')
        ssh_client.close()
        print("[INFO] Command executed successfully.")
        return output

    # ----------------------- CLOUD MONITORING ----------------------- #

    def monitor_aws_resources(self, aws_access_key, aws_secret_key, region):
        """
        Monitors AWS resources (instances, storage, etc.).

        Args:
            aws_access_key (str): AWS access key.
            aws_secret_key (str): AWS secret key.
            region (str): AWS region.

        Returns:
            dict: Resource monitoring data.
        """
        print(f"[INFO] Monitoring AWS resources in region: {region}")
        cloudwatch_client = boto3.client(
            'cloudwatch',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        metrics = cloudwatch_client.list_metrics()
        return metrics

    def summary(self):
        """
        Prints a summary of available cloud integration tools.
        """
        tools = [
            "AWS EC2 Instance Management",
            "GCP Cloud Storage Uploads",
            "Azure VM Management",
            "Private Cloud SSH Command Execution",
            "Cloud Resource Monitoring"
        ]
        print("[INFO] Cloud Integration Module Summary:")
        for tool in tools:
            print(f"- {tool}")
