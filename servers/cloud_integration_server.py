# Devin/servers/cloud_integration_server.py
# Purpose: A microservice to manage interactions with major cloud providers,
#          focusing on security and compliance checks.

import logging
import os
from typing import Dict, Any

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# --- Provider-specific SDKs ---
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_SDK_AVAILABLE = True
except ImportError:
    AWS_SDK_AVAILABLE = False

try:
    from google.cloud import storage
    from google.api_core import exceptions as gcp_exceptions
    GCP_SDK_AVAILABLE = True
except ImportError:
    GCP_SDK_AVAILABLE = False

try:
    from azure.storage.blob import BlobServiceClient
    from azure.core.exceptions import ResourceNotFoundError
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("CloudIntegrationServer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class CloudIntegrationServer:
    """
    Wraps a Flask application to provide a cloud security audit API.
    """
    def __init__(self):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required. 'pip install Flask'")
        
        # --- Initialize Clients (if SDKs are available) ---
        self.s3_client = boto3.client('s3') if AWS_SDK_AVAILABLE else None
        self.gcs_client = storage.Client() if GCP_SDK_AVAILABLE else None
        
        # --- Initialize Flask App ---
        self.app = Flask(__name__)
        self._register_routes()

    def _check_aws_s3(self, bucket_name: str) -> Dict:
        """Checks the public access configuration of an AWS S3 bucket."""
        if not self.s3_client: return {"error": "AWS SDK (boto3) not installed."}
        try:
            # 1. Check the Public Access Block configuration
            pub_block = self.s3_client.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
            if pub_block['BlockPublicAcls'] and pub_block['BlockPublicPolicy'] and pub_block['IgnorePublicAcls'] and pub_block['RestrictPublicBuckets']:
                return {"is_public": False, "reason": "Public Access Block is fully enabled at the bucket level."}

            # 2. If block is not fully enabled, check ACLs (more complex, simplified here)
            # A full check would also parse the Bucket Policy.
            acl = self.s3_client.get_bucket_acl(Bucket=bucket_name)
            for grant in acl['Grants']:
                grantee = grant.get('Grantee', {})
                uri = grantee.get('URI', '')
                if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                    return {"is_public": True, "reason": f"Bucket is public via ACL grant to '{uri}'."}

            return {"is_public": False, "reason": "Public Access Block is not fully enabled, but no public ACLs were found. Manual policy review is recommended."}
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                return {"error": "Bucket not found."}
            elif e.response['Error']['Code'] == 'AccessDenied':
                return {"error": "Access denied. Check your IAM permissions."}
            return {"error": str(e)}

    def _check_gcp_storage(self, bucket_name: str) -> Dict:
        """Checks the IAM policy of a Google Cloud Storage bucket."""
        if not self.gcs_client: return {"error": "GCP SDK (google-cloud-storage) not installed."}
        try:
            bucket = self.gcs_client.get_bucket(bucket_name)
            policy = bucket.get_iam_policy(requested_policy_version=3)
            public_roles = []
            for binding in policy.bindings:
                if "allUsers" in binding["members"] or "allAuthenticatedUsers" in binding["members"]:
                    public_roles.append(binding["role"])
            
            if public_roles:
                return {"is_public": True, "reason": f"Bucket is public via IAM roles: {public_roles}"}
            return {"is_public": False, "reason": "Bucket does not have public IAM bindings."}
        except gcp_exceptions.NotFound:
            return {"error": "Bucket not found."}
        except gcp_exceptions.Forbidden:
            return {"error": "Access denied. Check your IAM permissions."}
        except Exception as e:
            return {"error": str(e)}

    def _register_routes(self):
        """Defines the API endpoints for the server."""
        @self.app.route("/audit/aws/s3", methods=["POST"])
        def audit_aws_s3():
            data = request.get_json()
            if not data or "bucket_name" not in data:
                return jsonify({"error": "Missing 'bucket_name'."}), 400
            result = self._check_aws_s3(data['bucket_name'])
            return jsonify(result)

        @self.app.route("/audit/gcp/storage", methods=["POST"])
        def audit_gcp_storage():
            data = request.get_json()
            if not data or "bucket_name" not in data:
                return jsonify({"error": "Missing 'bucket_name'."}), 400
            result = self._check_gcp_storage(data['bucket_name'])
            return jsonify(result)

    def run(self, host: str = '127.0.0.1', port: int = 5003):
        """Starts the Flask web server."""
        logger.warning(f"Starting Cloud Integration Server on http://{host}:{port}")
        self.app.run(host=host, port=port)


if __name__ == "__main__":
    print("=========================================================")
    print("=== Cloud Integration Server Prototype ☁️🛡️ ===")
    print("=========================================================")
    print("!!! CRITICAL PREREQUISITES !!!")
    print("1. To use a provider, its Python SDK must be installed:")
    print("   pip install boto3 google-cloud-storage azure-storage-blob")
    print("2. You must be authenticated to the respective cloud provider in your shell:")
    print("   e.g., `aws configure`, `gcloud auth application-default login`, `az login`")

    print("\nThis script starts a server. To test it, run this script and then use")
    print("a tool like `curl` from a separate terminal window.\n")
    
    print("--- Example `curl` Commands ---")
    print("# To check an AWS S3 bucket:")
    print("curl -X POST -H \"Content-Type: application/json\" -d '{\"bucket_name\": \"my-s3-bucket-name\"}' http://127.0.0.1:5003/audit/aws/s3\n")
    print("# To check a GCP Cloud Storage bucket:")
    print("curl -X POST -H \"Content-Type: application/json\" -d '{\"bucket_name\": \"my-gcp-bucket-name\"}' http://127.0.0.1:5003/audit/gcp/storage\n")

    try:
        server = CloudIntegrationServer()
        print("Starting server now... (Press Ctrl+C to exit)")
        server.run(port=5003)
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
    
    print("\n=========================================================")
    print("=== Cloud Integration Server Prototype Complete ===")
    print("=========================================================")
