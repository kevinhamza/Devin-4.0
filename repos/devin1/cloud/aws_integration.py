"""
aws_integration.py
-------------------
This module provides integration and support for AWS cloud services.
Includes features for handling compute, storage, and AI-related services.
"""

import boto3
import os
import logging
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AWSIntegration")

class AWSIntegration:
    """
    AWS Integration class to manage interactions with AWS services.
    """

    def __init__(self):
        """
        Initializes AWSIntegration with environment credentials or configuration.
        """
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY")
        self.secret_key = os.getenv("AWS_SECRET_KEY")

        if not all([self.access_key, self.secret_key]):
            raise EnvironmentError("AWS_ACCESS_KEY and AWS_SECRET_KEY must be set as environment variables.")

        try:
            # Initialize clients for AWS services
            self.s3_client = boto3.client(
                "s3",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            self.ec2_client = boto3.client(
                "ec2",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            self.sagemaker_client = boto3.client(
                "sagemaker",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            logger.info("AWS Integration initialized successfully.")
        except NoCredentialsError:
            logger.error("No AWS credentials found.")
            raise
        except PartialCredentialsError:
            logger.error("Incomplete AWS credentials provided.")
            raise
        except Exception as e:
            logger.error(f"Error initializing AWS clients: {e}")
            raise

    def upload_file_to_s3(self, file_path, bucket_name, object_name=None):
        """
        Uploads a file to an S3 bucket.

        :param file_path: Path to the file to upload.
        :param bucket_name: Name of the S3 bucket.
        :param object_name: S3 object name. Defaults to file name.
        :return: True if upload succeeded, False otherwise.
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            self.s3_client.upload_file(file_path, bucket_name, object_name)
            logger.info(f"File '{file_path}' uploaded to bucket '{bucket_name}' as '{object_name}'.")
            return True
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except NoCredentialsError:
            logger.error("AWS credentials not found for S3 operation.")
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
        return False

    def create_ec2_instance(self, image_id, instance_type, key_name, security_group):
        """
        Launches an EC2 instance.

        :param image_id: AMI ID of the instance.
        :param instance_type: Instance type (e.g., 't2.micro').
        :param key_name: Key pair name for SSH access.
        :param security_group: Security group name or ID.
        :return: Instance ID if successful, None otherwise.
        """
        try:
            response = self.ec2_client.run_instances(
                ImageId=image_id,
                InstanceType=instance_type,
                KeyName=key_name,
                SecurityGroupIds=[security_group],
                MinCount=1,
                MaxCount=1
            )
            instance_id = response["Instances"][0]["InstanceId"]
            logger.info(f"EC2 instance launched with ID: {instance_id}")
            return instance_id
        except NoCredentialsError:
            logger.error("AWS credentials not found for EC2 operation.")
        except Exception as e:
            logger.error(f"Failed to launch EC2 instance: {e}")
        return None

    def deploy_sagemaker_model(self, model_name, role_arn, primary_container, endpoint_name):
        """
        Deploys a SageMaker model and creates an endpoint.

        :param model_name: Name of the SageMaker model.
        :param role_arn: AWS role ARN for SageMaker execution.
        :param primary_container: Primary container configuration for the model.
        :param endpoint_name: Name of the endpoint to create.
        :return: Endpoint name if successful, None otherwise.
        """
        try:
            # Create the model in SageMaker
            self.sagemaker_client.create_model(
                ModelName=model_name,
                PrimaryContainer=primary_container,
                ExecutionRoleArn=role_arn
            )
            logger.info(f"SageMaker model '{model_name}' created.")

            # Create the SageMaker endpoint configuration
            self.sagemaker_client.create_endpoint_config(
                EndpointConfigName=f"{endpoint_name}-config",
                ProductionVariants=[{
                    "VariantName": "AllTraffic",
                    "ModelName": model_name,
                    "InstanceType": "ml.t2.medium",
                    "InitialInstanceCount": 1
                }]
            )
            # Deploy the endpoint
            self.sagemaker_client.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=f"{endpoint_name}-config"
            )
            logger.info(f"SageMaker endpoint '{endpoint_name}' created.")
            return endpoint_name
        except NoCredentialsError:
            logger.error("AWS credentials not found for SageMaker operation.")
        except Exception as e:
            logger.error(f"Failed to deploy SageMaker model: {e}")
        return None
