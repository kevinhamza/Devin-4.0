# cloud/gcp_integration.py
"""
Google Cloud Platform (GCP) Integration Module
==============================================

This module provides comprehensive integration with Google Cloud Platform (GCP),
allowing the project to interact seamlessly with various GCP services such as Compute Engine,
Cloud Storage, BigQuery, Pub/Sub, and more.

The functionalities include service management, authentication, resource provisioning,
and usage monitoring.

Dependencies:
    - google-cloud-sdk
    - google-cloud-storage
    - google-cloud-bigquery
    - google-cloud-pubsub
"""

from google.cloud import storage, bigquery, pubsub_v1
import google.auth
import os
import logging

# Set up logging for better debugging and tracking
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GCPIntegration")

class GCPIntegration:
    def __init__(self, project_id=None, credentials_file=None):
        """
        Initialize the GCP integration module.

        Args:
            project_id (str): GCP project ID.
            credentials_file (str): Path to the GCP credentials JSON file.
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.credentials_file = credentials_file or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Attempt to load default credentials if available
        try:
            self.credentials, self.default_project = google.auth.default()
        except google.auth.exceptions.DefaultCredentialsError:
            logger.error("No valid credentials found. Please set up GCP authentication.")
            raise

        # If a credentials file is provided, use it for authentication
        if self.credentials_file:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_file
            logger.info(f"Using credentials from: {self.credentials_file}")

    def initialize_storage_client(self):
        """
        Initialize the Google Cloud Storage client.

        Returns:
            google.cloud.storage.Client: The storage client.
        """
        try:
            storage_client = storage.Client(project=self.project_id, credentials=self.credentials)
            logger.info("Google Cloud Storage client initialized.")
            return storage_client
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage client: {e}")
            raise

    def initialize_bigquery_client(self):
        """
        Initialize the BigQuery client.

        Returns:
            google.cloud.bigquery.Client: The BigQuery client.
        """
        try:
            bigquery_client = bigquery.Client(project=self.project_id, credentials=self.credentials)
            logger.info("Google BigQuery client initialized.")
            return bigquery_client
        except Exception as e:
            logger.error(f"Failed to initialize Google BigQuery client: {e}")
            raise

    def initialize_pubsub_client(self):
        """
        Initialize the Pub/Sub client.

        Returns:
            google.cloud.pubsub_v1.PublisherClient: The Pub/Sub publisher client.
            google.cloud.pubsub_v1.SubscriberClient: The Pub/Sub subscriber client.
        """
        try:
            publisher = pubsub_v1.PublisherClient(credentials=self.credentials)
            subscriber = pubsub_v1.SubscriberClient(credentials=self.credentials)
            logger.info("Google Pub/Sub client initialized.")
            return publisher, subscriber
        except Exception as e:
            logger.error(f"Failed to initialize Google Pub/Sub client: {e}")
            raise

    def upload_file_to_bucket(self, bucket_name, source_file_path, destination_blob_name):
        """
        Upload a file to a Google Cloud Storage bucket.

        Args:
            bucket_name (str): Name of the bucket.
            source_file_path (str): Path of the file to upload.
            destination_blob_name (str): Destination name for the file in the bucket.

        Returns:
            google.cloud.storage.blob.Blob: The uploaded blob object.
        """
        try:
            storage_client = self.initialize_storage_client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_path)
            logger.info(f"File {source_file_path} uploaded to {bucket_name}/{destination_blob_name}.")
            return blob
        except Exception as e:
            logger.error(f"Failed to upload file to bucket: {e}")
            raise

    def query_bigquery(self, query):
        """
        Run a query on BigQuery.

        Args:
            query (str): SQL query string.

        Returns:
            google.cloud.bigquery.table.RowIterator: Query results.
        """
        try:
            bigquery_client = self.initialize_bigquery_client()
            query_job = bigquery_client.query(query)
            logger.info("BigQuery query executed successfully.")
            return query_job.result()
        except Exception as e:
            logger.error(f"Failed to execute BigQuery query: {e}")
            raise

    def publish_message(self, topic_name, message):
        """
        Publish a message to a Pub/Sub topic.

        Args:
            topic_name (str): Name of the Pub/Sub topic.
            message (str): Message to publish.

        Returns:
            str: Message ID of the published message.
        """
        try:
            publisher, _ = self.initialize_pubsub_client()
            topic_path = publisher.topic_path(self.project_id, topic_name)
            future = publisher.publish(topic_path, message.encode("utf-8"))
            message_id = future.result()
            logger.info(f"Message published to topic {topic_name} with ID: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    def subscribe_to_topic(self, subscription_name, callback):
        """
        Subscribe to a Pub/Sub topic.

        Args:
            subscription_name (str): Name of the subscription.
            callback (function): Callback function to handle incoming messages.
        """
        try:
            _, subscriber = self.initialize_pubsub_client()
            subscription_path = subscriber.subscription_path(self.project_id, subscription_name)
            subscriber.subscribe(subscription_path, callback=callback)
            logger.info(f"Subscribed to Pub/Sub topic {subscription_name}.")
        except Exception as e:
            logger.error(f"Failed to subscribe to topic: {e}")
            raise

# Example Usage:
if __name__ == "__main__":
    try:
        gcp = GCPIntegration(project_id="your_project_id", credentials_file="path/to/credentials.json")

        # Example of uploading a file to a bucket:
        # gcp.upload_file_to_bucket("your_bucket_name", "local_file.txt", "remote_file.txt")

        # Example of running a query in BigQuery:
        # results = gcp.query_bigquery("SELECT * FROM your_dataset.your_table LIMIT 10")
        # for row in results:
        #     print(row)

        # Example of publishing a message to Pub/Sub:
        # message_id = gcp.publish_message("your_topic_name", "Hello, World!")
        # print("Message published with ID:", message_id)

    except Exception as e:
        logger.error(f"Error occurred: {e}")
